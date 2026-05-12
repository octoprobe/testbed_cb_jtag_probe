from __future__ import annotations

import base64
import dataclasses
import json
import logging
import pathlib

import altair as alt
import numpy as np
import pandas as pd

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

logger = logging.getLogger(__file__)


@dataclasses.dataclass
class Channel:
    name: str
    samples: np.ndarray  # dtype=uint8, values are 0 or 1


@dataclasses.dataclass
class Capture:
    channels: list[Channel]

    @staticmethod
    def from_file(filename: pathlib.Path) -> Capture:
        capture_dict = json.loads(filename.read_text(encoding="utf-8"))
        settings = capture_dict["Settings"]
        total_samples = int(settings["TotalSamples"])

        channels: list[Channel] = []
        for ch in settings["CaptureChannels"]:
            raw = base64.b64decode(ch["Samples"])
            assert len(raw) == total_samples
            # Some capture paths store bit masks (e.g. 16) instead of 1; normalize.
            normalized = np.frombuffer(raw, dtype=np.uint8) != 0
            channels.append(
                Channel(name=ch["ChannelName"], samples=normalized.view(np.uint8))
            )

        return Capture(channels=channels)

    def to_dataframe(self) -> pd.DataFrame:
        lengths = {len(ch.samples) for ch in self.channels}
        assert len(lengths) == 1, f"Channels have differing sample counts: {lengths}"
        sample_index = np.arange(lengths.pop(), dtype=np.int32)

        frames = []
        for channel in self.channels:
            frames.append(
                pd.DataFrame(
                    {
                        "sample": sample_index,
                        "channel_name": channel.name,
                        "value": channel.samples,
                    }
                )
            )
        return pd.concat(frames, ignore_index=True)


def test_altair() -> None:
    filename_capture = DIRECTORY_OF_THIS_FILE / "capture-gusmanb/capture.lac"
    assert filename_capture.exists()

    capture = Capture.from_file(filename_capture)

    assert capture.channels
    for channel in capture.channels:
        assert set(channel.samples) <= {0, 1}

    df = capture.to_dataframe()

    base = (
        alt.Chart(df, width=800, height=50)
        .mark_line()
        .encode(
            alt.X("sample:Q").title("Sample"),
            alt.Y("value:Q")
            .scale(domain=(0, 1))
            .axis(values=[0, 1], format="d", title=None),
        )
    )

    chart = (
        alt.layer(base)
        .facet(
            row=alt.Row("channel_name:N")
            .sort([ch.name for ch in capture.channels])
            .title(None),
        )
        .properties(title="Logic capture per channel")
    )

    output_path = DIRECTORY_OF_THIS_FILE / "capture-gusmanb" / "capture_altair.svg"
    chart.save(str(output_path))
    assert output_path.exists()
