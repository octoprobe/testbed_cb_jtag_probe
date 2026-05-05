from __future__ import annotations

import dataclasses
import logging
import pathlib
import typing

from octoprobe.lib_tentacle import TentacleBase
from octoprobe.lib_tentacle_debugprobe import TentacleSigrokPico
from octoprobe.usb_tentacle.usb_tentacle import UsbTentacle
from octoprobe.util_baseclasses import TentacleInstance, TentacleSpecBase
from octoprobe.util_constants import TAG_MCU
from octoprobe.util_firmware_spec import FirmwareDownloadSpec
from octoprobe.util_pytest.util_func_logger import func_logger
from octoprobe.util_pyudev import UdevPoller

from .constants import (
    FILENAME_DUT_MAIN,
    TAG_BOARD,
    TAG_BUILD_VARIANTS,
)

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
FILENAME_DUT_FIRWARE_SPEC = DIRECTORY_OF_THIS_FILE / "util_tentacle_dut_firmware.json"

I2C_ADDRESS_Tguard = 0x48
I2C_ADDRESS_Tref = 0x49
I2C_ADDRESS_EEPROM = 0x50
I2C_ADDRESS_OFFSET_DISCONNECT = 4


@dataclasses.dataclass(frozen=True, repr=True, eq=True, order=True)
class TentacleSpecJtagProbe(TentacleSpecBase):
    @property
    def micropython_board(self) -> str:
        """
        If
          tags="board=ESP8266_GENERIC, ..."
        is defined, it will be used.
        Fallback to 'tentacle_tag'.
        """
        board = self.get_tag(TAG_BOARD)
        if board is not None:
            return board
        return self.tentacle_tag

    @property
    def description(self) -> str:
        mcu = self.get_tag(TAG_MCU)
        if mcu is None:
            return self.micropython_board
        return mcu + "/" + self.micropython_board

    @property
    def build_variants(self) -> list[str]:
        """
        Example for PICO: ["", "RISCV"]
        Example for ESP8266_GENERIC: [""]
        """
        variants = self.get_tag(TAG_BUILD_VARIANTS)
        if variants is None:
            return [""]
        return variants.split(":")


@dataclasses.dataclass
class Inject:
    inject_Tguard_disconnect: bool = False
    """
    True: Change the I2C address of Tguard to make it 'invisible'
    """
    inject_Tref_disconnect: bool = False
    """
    True: Change the I2C address of Tref to make it 'invisible'
    """
    inject_EEPROM_disconnect: bool = False
    """
    True: Change the I2C address of EEPROM to make it 'invisible'
    """
    inject_T_limit: bool = False
    """
    Open collector.
    False: open
    True: closed
    """
    sim_temperature_C: float | None = None
    """
    Start a LM75B I2C target simulator.
    Simulates Tguard/Tref wether on 'inject_Tgard/Tref_disconnect' is set.
    """
    sim_EEPROM_data: str | None = None
    """
    Start a EEPROM I2C target simulator
    """

    def __post_init__(self) -> None:
        assert isinstance(self.inject_Tguard_disconnect, bool)
        assert isinstance(self.inject_Tref_disconnect, bool)
        assert isinstance(self.inject_EEPROM_disconnect, bool)
        assert isinstance(self.inject_T_limit, bool)
        assert isinstance(self.sim_temperature_C, float | None)
        assert isinstance(self.sim_EEPROM_data, str | None)
        i2c_target_count = sum(
            (
                self.inject_Tguard_disconnect,
                self.inject_Tref_disconnect,
                self.inject_EEPROM_disconnect,
            )
        )
        assert i2c_target_count <= 1, "Only one I2C target may be simulated."
        if self.sim_temperature_C is not None:
            assert self.inject_Tguard_disconnect or self.inject_Tref_disconnect, (
                "If sim_temperature_C is given, a real sensor must be disconnected too."
            )
        if self.sim_EEPROM_data is not None:
            assert self.inject_EEPROM_disconnect, (
                "If sim_EEPROM_data is given, the real eeprom must be disconnected tool."
            )


class TentacleJTAG(TentacleBase):  # pylint: disable=too-many-public-methods
    def __init__(
        self,
        tentacle_instance: TentacleInstance,
        usb_tentacle: UsbTentacle,
    ) -> None:
        super().__init__(
            tentacle_instance=tentacle_instance,
            usb_tentacle=usb_tentacle,
        )

    @staticmethod
    def factory_usb_tentacle(usb_tentacle: UsbTentacle) -> TentacleJTAG:
        """
        Create a temporary TentacleInfra
        """
        assert isinstance(usb_tentacle, UsbTentacle)
        # pylint: disable=import-outside-toplevel
        from .tentacles_inventory import TENTACLES_INVENTORY

        tentacle_instance = TENTACLES_INVENTORY.get_by_serial_delimited(
            usb_tentacle.serial_delimited
        )
        tentacle = TentacleJTAG(
            tentacle_instance=tentacle_instance,
            usb_tentacle=usb_tentacle,
        )
        tentacle.tentacle_state.firmware_spec = FirmwareDownloadSpec.factory2(
            FILENAME_DUT_FIRWARE_SPEC
        )
        return tentacle

    @property
    def sigrok_pico(self) -> TentacleSigrokPico:
        assert isinstance(self._probe, TentacleSigrokPico)
        return self._probe

    @property
    @typing.override
    def pytest_id(self) -> str:
        """
        Example: 1831
        """
        return f"{self.tentacle_serial_short}-{self.tentacle_instance.solder_version}"

    @property
    def tentacle_spec(self) -> TentacleSpecJtagProbe:
        """TentacleHeatguard
        Just does typcasting from TentacleSpecBase to TentacleSpecHeatguard
        """
        tentacle_spec_base = self.tentacle_spec_base
        assert isinstance(tentacle_spec_base, TentacleSpecJtagProbe)
        return tentacle_spec_base

    def copy_micropython_main(self, restart_dut: bool) -> None:
        src = FILENAME_DUT_MAIN
        logger.info(f"{self.dut.label}: Copy {src}")
        self.dut.mp_remote.cp(src=src, dest=":", multiple=False)
        if restart_dut:
            # Restart main
            self.dut.mp_remote.exec_raw(
                cmd="import machine; machine.reset()",
                follow=False,
            )

    def flash_dut_zephyr(
        self,
        firmware: pathlib.Path,
        directory_logs: pathlib.Path,
    ) -> None:
        # pylint: disable=import-outside-toplevel
        from octoprobe import util_mcu_pico

        assert self.dut is not None

        assert isinstance(firmware, pathlib.Path)
        assert isinstance(directory_logs, pathlib.Path)
        if not firmware.is_file():
            logger.error(f"Firmware does not exist: {firmware}")
            return

        with UdevPoller() as udev:
            programmer = util_mcu_pico.DutProgrammerPicotool()
            event = programmer.enter_boot_mode(tentacle=self, udev=udev)
            util_mcu_pico.picotool_flash(
                event=event,
                directory_logs=directory_logs,
                filename_firmware=firmware,
            )

    @func_logger
    def set_power_dut(
        self,
        on: bool,
        udev: UdevPoller,
        start_dut_main: bool = True,
    ) -> str:
        logger.info(f"[COLOR_INFO]set_power_dut({on=} {start_dut_main=})")

        if on:
            # Power on DUT
            self.infra.power_dut_off_and_wait()

            tty = self.dut.dut_mcu.application_mode_power_up(tentacle=self, udev=udev)
            logger.info(f"{self.dut.label}: Powered up: {tty}")
            return tty

        self.infra.power_dut_off_and_wait()
        return ""
