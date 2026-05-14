import logging

from octoprobe.util_pyudev import UdevPoller

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


def test_ok(dut_power_up: TentacleJTAG) -> None:
    """
    Rationale: Behaviour when the temperature difference of both sensor get too high
    Expected transitons: INIT -> OK
    """
    # The fixture 'dut_power_up' already tests this...

    # tty = dut_power_up.set_power_dut(on=True, udev=udev)

    dut_power_up.sigrok_pico.label

    dut_power_up.sigrok_pico.tty
    dut_power_up.dut.mp_remote.exec_raw(MICROPYTHON_CODE)
