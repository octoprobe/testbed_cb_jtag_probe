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
    pre_trigger_samples: int
    total_samples: int

    @staticmethod
    def from_file(filename: pathlib.Path) -> Capture:
        capture_dict = json.loads(filename.read_text(encoding="utf-8"))
        settings = capture_dict["Settings"]
        total_samples = int(settings["TotalSamples"])
        pre_trigger_samples = int(settings["PreTriggerSamples"])

        channels: list[Channel] = []
        for ch in settings["CaptureChannels"]:
            raw = base64.b64decode(ch["Samples"])
            assert len(raw) == total_samples
            # Some capture paths store bit masks (e.g. 16) instead of 1; normalize.
            normalized = np.frombuffer(raw, dtype=np.uint8) != 0
            channels.append(
                Channel(name=ch["ChannelName"], samples=normalized.view(np.uint8))
            )
            # normalized = np.frombuffer(raw, dtype=np.uint8)
            # channels.append(Channel(name=ch["ChannelName"], samples=normalized))

        return Capture(
            channels=channels,
            pre_trigger_samples=pre_trigger_samples,
            total_samples=total_samples,
        )

    def to_dataframe(self) -> pd.DataFrame:
        sample_index = np.arange(self.total_samples, dtype=np.int32)

        frames = [
            pd.DataFrame(
                {
                    "sample": sample_index,
                    "channel_name": channel.name,
                    "value": channel.samples,
                }
            )
            for channel in self.channels
        ]
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
            .axis(
                values=[0, 1],
                format="d",
                title=None,
            ),
        )
    )

    trigger_line = (
        alt.Chart(
            pd.DataFrame(
                {
                    "sample": [capture.pre_trigger_samples],
                    "y": [-0.2],
                    "y2": [1.2],
                }
            )
        )
        .mark_rule(color="red")
        .encode(
            alt.X("sample:Q"),
            alt.Y("y:Q"),
            alt.Y2("y2:Q"),
        )
    )

    chart = (
        alt.layer(base, trigger_line)
        .facet(
            row=alt.Row("channel_name:N")
            .sort([ch.name for ch in capture.channels])
            .title(None),
            data=df,
        )
        .properties(title="Logic capture per channel")
    )

    output_path = DIRECTORY_OF_THIS_FILE / "capture-gusmanb" / "capture_altair.svg"
    chart.save(str(output_path))
    assert output_path.exists()
