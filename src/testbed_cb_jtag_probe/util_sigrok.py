from __future__ import annotations

import logging
import os
import stat
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import urlretrieve

from . import constants

logger = logging.getLogger(__file__)

DIRECTORY_DOWNLOADS_SIGROK = constants.DIRECTORY_DOWNLOADS / "sigrok"
DIRECTORY_DOWNLOADS_SIGROK.mkdir(parents=True, exist_ok=True)

APPIMAGE_SIGROK_CLI = "sigrok-cli-NIGHTLY-x86_64-debug.appimage"
APPIMAGE_PULSEVIEW = "pulseview-NIGHTLY-x86_64-release.appimage"

DIRECTORY_SIGROKDECODE = (
    constants.DIRECTORY_REPO / "src" / "testbed_cb_jtag_probe" / "sigrok_decoders"
)
assert DIRECTORY_SIGROKDECODE.is_dir()


def download_sigrok(url_base: str) -> None:
    logger.info(f"Download from: {url_base}")
    logger.info(f"  to: {DIRECTORY_DOWNLOADS_SIGROK}")

    def download_appimage(appimage: str) -> None:
        url = url_base + "/" + appimage

        filename = DIRECTORY_DOWNLOADS_SIGROK / appimage
        try:
            _tmp_filename, _headers = urlretrieve(url=url, filename=filename)
        except HTTPError as e:
            raise ValueError(f"{url_base}: {e}") from e
        logger.info(f"    {filename.name}: {filename.stat().st_size / 1e6:0.1f} MBytes")
        filename.with_suffix(".txt").write_text(f"url: {url}")

        # chmod a+x ..
        filename.chmod(
            filename.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )

    for appimage in (APPIMAGE_SIGROK_CLI, APPIMAGE_PULSEVIEW):
        download_appimage(appimage=appimage)


def call(name: str, binary: str, args: list[str]) -> None:
    executable = DIRECTORY_DOWNLOADS_SIGROK / binary
    command = [name, *args]
    print(" / ".join(command))

    def selector(k: str) -> bool:
        if k in ("PATH", "DISPLAY"):
            return True
        if k.startswith("XDG_"):
            return True
        return False

    env = {k: v for k, v in os.environ.items() if selector(k)}
    env["SIGROKDECODE_DIR"] = str(DIRECTORY_SIGROKDECODE)
    rc = subprocess.call(
        executable=executable,
        args=command,
        env=env,
        cwd=constants.DIRECTORY_REPO,
    )
    sys.exit(rc)


def call_sigrok_cli(args: list[str]) -> None:
    call(name="sigrok-cli", binary=APPIMAGE_SIGROK_CLI, args=args)


def call_pulseview(args: list[str]) -> None:
    call(name="pulseview", binary=APPIMAGE_PULSEVIEW, args=args)
