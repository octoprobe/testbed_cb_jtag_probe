from __future__ import annotations

from octoprobe import util_mcu_pico

from testbed_cb_jtag_probe.constants import EnumFut, EnumTentacleType

from .tentacle_spec import TentacleSpecJtagProbe

MCU_JTAGPROBE = TentacleSpecJtagProbe(
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="MCU_HEADGUARD",
    futs=[EnumFut.FUT_PROBE],
    doc="",
    mcu_usb_id=util_mcu_pico.RPI_PICO2_USB_ID,
    tags="boards=RPI_PICO,mcu=rp2,programmer=picotool,probe=sigrok-pico",
    relays_closed={
        EnumFut.FUT_MCU_ONLY: [],
    },
)
