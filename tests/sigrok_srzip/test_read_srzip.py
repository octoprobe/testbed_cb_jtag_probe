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


def test_read_srzip() -> None:
    filename_srzip = (
        DIRECTORY_OF_THIS_FILE
        / "sigrok-dumps/i2c/sensirion_sht2x/sensirion_sht21_humidity35.sr"
    )
    assert filename_srzip.exists()
