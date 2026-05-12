import base64
import json
import logging
import pathlib

import altair as alt
import pandas as pd

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

logger = logging.getLogger(__file__)


def test_altair() -> None:
    filename_capture = DIRECTORY_OF_THIS_FILE / "capture-gusmanb/capture.lac"
    assert filename_capture.exists()

    capture_dict = json.loads(filename_capture.read_text(encoding="utf-8"))
    settings = capture_dict["Settings"]
    capture_channels = settings["CaptureChannels"]

    total_samples = int(settings["TotalSamples"])

    extracted_rows: list[dict] = []
    for channel in capture_channels:
        channel_name: str = channel["ChannelName"]
        encoded_samples = channel["Samples"]
        raw_samples = base64.b64decode(encoded_samples)

        assert len(raw_samples) == total_samples

        for sample_index, raw_value in enumerate(raw_samples):
            # Some capture paths store bit masks (e.g. 16) instead of 1; normalize.
            value = 1 if raw_value != 0 else 0
            extracted_rows.append(
                {
                    "sample": sample_index,
                    "channel": channel_name,
                    "value": value,
                }
            )

    assert extracted_rows
    assert len(extracted_rows) == len(capture_channels) * total_samples
    assert {row["value"] for row in extracted_rows} <= {0, 1}

    df = pd.DataFrame(extracted_rows)

    base = (
        alt.Chart(df, width=800, height=80)
        .mark_line()
        .encode(
            alt.X("sample:Q").title("Sample"),
            alt.Y("value:Q").scale(domain=(0, 1)).axis(tickCount=2).title("Level"),
        )
    )

    chart = (
        alt.layer(base)
        .facet(
            facet=alt.Facet("channel:N")
            .sort([ch["ChannelName"] for ch in capture_channels])
            .title(None),
            columns=1,
        )
        .properties(title="Logic capture per channel")
    )

    output_path = DIRECTORY_OF_THIS_FILE / "capture-gusmanb" / "capture_altair.svg"
    chart.save(str(output_path))
    assert output_path.exists()
