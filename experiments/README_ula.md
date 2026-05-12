# Logic Analyzer

## Ula

* Pretriggering seems not to work. Entering a percentage will posttrigger.
* Trigger works nice for the first shot
* For repetitive signal, trigger seems to be quite random and the signal is sometimes broken.
* The signal toggles quite often...

* For the 100Hz signal:
  * 10 kSamples
  * 500 kHz

```bash
testbed_cb_jtag_probe flash-ula
testbed_cb_jtag_probe flash-jtag --firmware-url=https://micropython.org/resources/firmware/RPI_PICO2-20260406-v1.28.0.uf2
op power --on dut --on proberun
op query
mpremote connect /dev/ttyACM2 run experiments/micropython_ula_test_main.py
~/experiment/experiment_sigrok/appimage_sigrok/pulseview-NIGHTLY-x86_64-debug.AppImage
```

```bash
downloads/sigrok-cli-NIGHTLY-x86_64-debug.appimage --driver ols:conn=/dev/ttyACM1 --show
Driver functions:
    Logic analyzer
Scan options:
    conn
    serialcomm
    probe_names
ols:conn=/dev/ttyACM1 - uLA: Micro Logic Analyzer with 16 channels: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
Supported configuration options:
    conn: /dev/ttyACM1 (current)
    Maximum number of samples: 100000
    samplerate (10 Hz - 100 MHz in steps of 1 Hz)
    Supported triggers: 0 1 
    captureratio: 0 (current)
    external_clock: on, off (current)
    clock_edge: rising (current), falling
    pattern: None (current), External, Internal
    swap: on, off
    rle: on, off (current)
```


Capture
```bash
op power --off dut --off proberun
sleep 1
op power --on proberun
sleep 1
op power --on dut --on proberun
sleep 1
op query
downloads/sigrok-cli-NIGHTLY-x86_64-debug.appimage \
  --driver ols:conn=/dev/ttyACM1 \
  --loglevel 5 \
  --config samplerate=500k \
  --channels 0=A0,1=A1,2=A2,3=A3 \
  --triggers A0=1 \
  --wait-trigger \
  --samples 100000 \
  -o capture.sr
mpremote connect /dev/ttyACM2 run experiments/micropython_ula_test_main.py

downloads/pulseview-NIGHTLY-x86_64-release.appimage -i capture.sr
```


$ sigrok-cli -i capture.sr --show
Samplerate: 50000000
Channels: 16
- 0: logic
...
- 15: logic
Logic unitsize: 4
Logic sample count: 72468

```

## sigrok-pico

```bash
testbed_cb_jtag_probe flash-ula --firmware-url=https://micropython.org/resources/firmware/RPI_PICO2-20260406-v1.28.0.uf2
testbed_cb_jtag_probe flash-jtag --firmware-url=https://micropython.org/resources/firmware/RPI_PICO2-20260406-v1.28.0.uf2
op power --on dut --on proberun
op query
mpremote connect /dev/ttyACM2 run experiments/micropython_ula_test_main.py
~/experiment/experiment_sigrok/appimage_sigrok/pulseview-NIGHTLY-x86_64-debug.AppImage
```
