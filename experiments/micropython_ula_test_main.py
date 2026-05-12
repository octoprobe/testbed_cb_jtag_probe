# For any generic python board
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
# time.sleep(0.1)
# for pwm in pwms:
#     pwm.deinit()
