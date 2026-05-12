import logging
import pathlib
import base64
import json
from testbed_cb_jtag_probe import constants

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

logger = logging.getLogger(__file__)


def test_altair() -> None:
    filename_capture = DIRECTORY_OF_THIS_FILE / "capture-gusmanb/capture.lac"
    assert filename_capture.exists()

    capture_dict = json.loads(filename_capture.read_text(encoding="utf-8"))
    settings = capture_dict["Settings"]
    capture_channels = settings["CaptureChannels"]

    total_samples = int(settings["TotalSamples"])

    extracted_rows: list[dict[str, int]] = []
    for channel in capture_channels:
        channel_number = int(channel["ChannelNumber"])
        encoded_samples = channel["Samples"]
        raw_samples = base64.b64decode(encoded_samples)

        assert len(raw_samples) == total_samples

        for sample_index, raw_value in enumerate(raw_samples):
            # Some capture paths may store bit masks (for example 16) instead of 1.
            value = 1 if raw_value != 0 else 0
            extracted_rows.append(
                {
                    "sample": sample_index,
                    "channel_number": channel_number,
                    "value": value,
                }
            )

    assert extracted_rows
    assert len(extracted_rows) == len(capture_channels) * total_samples
    assert {row["value"] for row in extracted_rows} <= {0, 1}
