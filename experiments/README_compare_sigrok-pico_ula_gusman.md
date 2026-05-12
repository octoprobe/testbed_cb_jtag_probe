# Compare pico logic analyzers

* https://github.com/gusmanb/logicanalyzer
* https://github.com/dotcypress/ula
* https://github.com/pico-coder/sigrok-pico


For your use case — **8 JTAG digital lines, command-line capture, and especially reliable pre-trigger capture** — I would choose [μLA (dotcypress/ula)](https://github.com/dotcypress/ula?utm_source=chatgpt.com) over [sigrok-pico](https://github.com/pico-coder/sigrok-pico?utm_source=chatgpt.com).

Here’s the practical comparison.

| Feature                        | sigrok-pico                                        | μLA                                        |
| ------------------------------ | -------------------------------------------------- | ------------------------------------------ |
| Primary design goal            | General sigrok integration + oscilloscope features | Dedicated logic analyzer                   |
| Max channels                   | Up to 21 digital ([DeepWiki][1])                   | 16 digital ([GitHub][2])                   |
| Sampling rate                  | Good, but varies by mode                           | 100 MHz stable design target ([GitHub][2]) |
| Triggering                     | Basic sigrok trigger support                       | Hardware PIO fast triggers ([GitHub][2])   |
| Pre-trigger behavior           | Less emphasized/documented                         | Core feature of SUMP-style capture         |
| sigrok-cli support             | Native sigrok driver                               | Via OLS/SUMP backend                       |
| Maturity for LA-only workflows | Experimental-ish                                   | Very focused and simple                    |
| Buffer model                   | More complex DMA streaming                         | Fixed acquisition RAM                      |
| Command-line ergonomics        | OK                                                 | Very good with `sigrok-cli -d ols:`        |
| JTAG capture suitability       | Good                                               | Excellent                                  |
| Deterministic trigger latency  | Moderate                                           | Better                                     |

The key thing for you is this:

* **μLA uses the old SUMP/OpenBench Logic Sniffer model**, which was specifically designed around:

  * trigger positioning
  * pre-trigger buffering
  * deterministic capture windows

* JTAG debugging often needs:

  * “show me 10k samples before TMS rises”
  * or “capture before TAP reset”
  * or “see the transition leading into a state change”

That aligns extremely well with the SUMP architecture.

Meanwhile, `sigrok-pico` is more:

* “turn RP2040 into a general-purpose sigrok device”
* broader feature set
* less optimized around deep trigger workflows

For your exact workload, simpler is better.

Example workflow with μLA + sigrok-cli:

```bash
sigrok-cli \
  -d ols:conn=/dev/ttyACM0 \
  --config samplerate=50m \
  --channels 0,1,2,3,4,5,6,7 \
  --triggers 0=r \
  --samples 200000 \
  -o capture.sr
```

Then decode JTAG:

```bash
sigrok-cli -i capture.sr -P jtag
```

The important architectural difference:

* μLA captures into RAM first, then uploads
* which makes trigger-relative timing more deterministic

That matters much more than raw sample rate for JTAG.

A few additional notes:

* 100 MHz is plenty for most embedded JTAG.
* RP2040 RAM limits total depth (~200 KB on μLA). ([GitHub][2])
* At 8 channels:

  * 200 KB ≈ 200k samples
  * at 50 MHz → ~4 ms window
* Usually enough for TAP transitions and command sequences.

One caveat:

* SUMP trigger support in sigrok-cli is older and somewhat primitive.
* If you need:

  * protocol-aware triggers
  * very deep pre-trigger history
  * multi-stage triggering
  * streaming captures
    then eventually you outgrow RP2040-class analyzers.

In that case:

* DSLogic hardware
* or FPGA analyzers
  become worthwhile.

But for:

* embedded JTAG
* OpenOCD interactions
* TAP debugging
* reset sequencing
* SWD/JTAG reverse engineering

μLA is probably the cleanest RP2040 solution right now.

[1]: https://deepwiki.com/pico-coder/sigrok-pico?utm_source=chatgpt.com "pico-coder/sigrok-pico | DeepWiki"
[2]: https://github.com/dotcypress/ula?utm_source=chatgpt.com "GitHub - dotcypress/ula: μLA: Micro Logic Analyzer for RP2040"
