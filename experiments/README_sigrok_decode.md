# Sigrok decode

Links

* [sigrok-cli parameters](https://sigrok.org/wiki/Protocol_decoder:I2c)

## Decode I2C

```bash
sigrok-cli --protocol-decoders=i2c:scl=SCL:sda=SDA --input-file ./tests/sigrok_srzip/sigrok-dumps/i2c/nxp_pca9571/pca9571_simple.sr


sigrok-cli --protocol-decoders=i2c:scl=TDI:sda=TDO --input-format=csv --input-file capture.csv
```

## Convert SR -> CSV

```bash
sigrok-cli --input-file ./tests/sigrok_srzip/sigrok-dumps/i2c/nxp_pca9571/pca9571_simple.sr --output-format csv --output-file ./tests/sigrok_srzip/sigrok-dumps/i2c/nxp_pca9571/pca9571_simple.csv

sigrok-cli --input-file ./tests/sigrok_srzip/sigrok-dumps/i2c/nxp_pca9571/pca9571_sequence.sr --output-format csv --output-file ./tests/sigrok_srzip/sigrok-dumps/i2c/nxp_pca9571/pca9571_sequence.csv
```

**Decode I2C**

```bash
sigrok-cli --protocol-decoders=i2c:scl=SCL:sda=SDA --input-file ./tests/sigrok_srzip/sigrok-dumps/i2c/nxp_pca9571/pca9571_simple.sr
...
i2c-1: 0
i2c-1: 1
i2c-1: 1
i2c-1: Data write: D0
i2c-1: ACK
i2c-1: Stop

# Manually update headers in pca9571_simple.csv

sigrok-cli --protocol-decoders=i2c:scl=SCL:sda=SDA --input-format csv --input-file ./tests/sigrok_srzip/sigrok-dumps/i2c/nxp_pca9571/pca9571_simple.csv
...
i2c-1: 0
i2c-1: 1
i2c-1: 1
i2c-1: Data write: D0
i2c-1: ACK
i2c-1: Stop
```
