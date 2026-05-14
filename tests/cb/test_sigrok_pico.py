import logging

from octoprobe.util_pytest.util_resultdir import ResultsDir

from testbed_cb_jtag_probe import util_sigrok
from testbed_cb_jtag_probe.tentacle_spec import TentacleJTAG

logger = logging.getLogger(__file__)

MICROPYTHON_CODE = """
from machine import Pin
from machine import PWM
import time

# 'trig1' triggers the DAQ. So we initialize it last!
ticks_ms = int((2**16) / 10)
pwms = [
    PWM(Pin("GPIO12"), freq=100, duty_u16=4 * ticks_ms),
    PWM(Pin("GPIO13"), freq=100, duty_u16=3 * ticks_ms),
    PWM(Pin("GPIO14"), freq=100, duty_u16=2 * ticks_ms),
    PWM(Pin("GPIO15"), freq=100, duty_u16=1 * ticks_ms),
]
time.sleep(0.2)
for pwm in pwms:
    pwm.deinit()
"""


def test_ok(dut_power_up: TentacleJTAG, testresults_directory: ResultsDir) -> None:
    """
    Rationale: Behaviour when the temperature difference of both sensor get too high
    Expected transitons: INIT -> OK
    """
    # The fixture 'dut_power_up' already tests this...

    # tty = dut_power_up.set_power_dut(on=True, udev=udev)

    args = [
        f"--driver=raspberrypi-pico:conn={dut_power_up.sigrok_pico.tty}:serialcomm=115200/flow=0",
        "--channels=D2=TDI,D3=TDO,D4=TCK,D5=TMS",
        "--config=samplerate=10MHz",
        "--config=captureratio=30",
        "--samples=200k",
        "--wait-trigger",
        "--triggers=TCK=r",
        "--protocol-decoders=jtag",
        "--output-file=capture.sr",
    ]
    rc = util_sigrok.call_appimage(
        util_sigrok.APPIMAGE_SIGROK_CLI,
        args=args,
        cwd=str(testresults_directory.directory_test),
        timeout_s=5.0,
    )
    assert rc == 0

    dut_power_up.dut.mp_remote.exec_raw(MICROPYTHON_CODE)
