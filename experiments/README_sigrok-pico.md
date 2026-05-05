# Sigrok-pico

Links

* https://github.com/pico-coder/sigrok-pico
* https://github.com/pico-coder/sigrok-pico/blob/main/GettingStarted.md
* [channel vs GPIO](https://github.com/pico-coder/sigrok-pico/blob/main/AnalyzerDetails.md)
* https://github.com/pico-coder/sigrok-pico/tree/main/pico_sdk_sigrok/release
* https://github.com/pico-coder/sigrok-pico/blob/main/pico_sdk_sigrok/release/pico_original.uf2
* https://github.com/sigrokproject/libsigrok/tree/master/src/hardware/raspberrypi-pico

## Channels

See https://github.com/pico-coder/sigrok-pico/blob/main/AnalyzerDetails.md
Digital channels are PICO board pins D2-D22 and are named accordingly in sigrok.


## Test with pulseview

```bash
testbed_cb_jtag_probe flash-logic-analyzer
testbed_cb_jtag_probe flash-jtag --firmware-url=https://micropython.org/resources/firmware/RPI_PICO2-20260406-v1.28.0.uf2

op power --off dut --off proberun
sleep 1
op power --on proberun
sleep 1
op power --on dut --on proberun
sleep 1
op query
mpremote connect /dev/ttyACM2 run experiments/micropython_ula_test_main.py

downloads/sigrok/pulseview-NIGHTLY-x86_64-release.appimage
# Device settings
## RaspberryPI Pico (raspberrypi-pico)
## Serial Port: /dev/ttyACM1 (Pico - DE...)
## Raspberry Pi PICO with 24 channels

## Name channels TDI, TDO, TCK, TMS
## Stack JTAG decoder

## 200k samples
## 10MHz

downloads/sigrok/sigrok-cli-NIGHTLY-x86_64-debug.appimage \
    --driver raspberrypi-pico:conn=/dev/ttyACM1:serialcomm=115200/flow=0 \
    --channels D2=TDI,D3=TDO,D4=TCK,D5=TMS \
    --config samplerate=10MHz \
    --config captureratio=30 \
    --samples 200k \
    --wait-trigger \
    --triggers TCK=r \
    --protocol-decoders=jtag \
    --output-file capture.sr

downloads/sigrok/pulseview-NIGHTLY-x86_64-release.appimage capture.sr
```