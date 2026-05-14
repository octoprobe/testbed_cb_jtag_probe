from __future__ import annotations

import dataclasses
import io
import logging
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from urllib.request import urlretrieve

from . import constants

logger = logging.getLogger(__file__)

DIRECTORY_DOWNLOADS_SIGROK = constants.DIRECTORY_DOWNLOADS / "sigrok"
DIRECTORY_DOWNLOADS_SIGROK.mkdir(parents=True, exist_ok=True)

DIRECTORY_SIGROKDECODE = (
    constants.DIRECTORY_REPO / "src" / "testbed_cb_jtag_probe" / "sigrok_decoders"
)
assert DIRECTORY_SIGROKDECODE.is_dir()


@dataclasses.dataclass(frozen=True, repr=True, slots=True)
class AppImage:
    prog: str
    binary: str

    @property
    def executable(self) -> pathlib.Path:
        return DIRECTORY_DOWNLOADS_SIGROK / self.binary


APPIMAGE_SIGROK_CLI = AppImage("sigrok-cli", "sigrok-cli-NIGHTLY-x86_64-debug.appimage")
APPIMAGE_PULSEVIEW = AppImage("pulseview", "pulseview-NIGHTLY-x86_64-release.appimage")


def download_sigrok(url_base: str) -> None:
    logger.info(f"Download from: {url_base}")
    logger.info(f"  to: {DIRECTORY_DOWNLOADS_SIGROK}")

    def download_appimage(binary: str) -> None:
        url = url_base + "/" + binary

        filename = DIRECTORY_DOWNLOADS_SIGROK / binary
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
        download_appimage(binary=appimage.binary)


def popen_appimage(
    appimage: AppImage,
    args: list[str],
    cwd: str | None = None,
    logfile: pathlib.Path | None = None,
) -> RunPopen:
    """
    Call sigrok binaries with
    * specific env
    * log output
    """

    def env_filter(k: str) -> bool:
        if k in ("PATH", "DISPLAY"):
            return True
        if k.startswith("XDG_"):
            return True
        return False

    env = {k: v for k, v in os.environ.items() if env_filter(k)}
    env["SIGROKDECODE_DIR"] = str(DIRECTORY_SIGROKDECODE)

    return RunPopen(
        args=args,
        env=env,
        executable=str(appimage.executable),
        cwd=cwd,
        logfile=logfile,
    )


class RunPopen:
    def __init__(
        self,
        args: list[str],
        env: dict[str, str] | None = None,
        executable: str | None = None,
        cwd: str | None = None,
        logfile: pathlib.Path | None = None,
    ) -> None:
        """
        The program (stdout and stderr will be written to a logfile.
        if logfile is given it will be used, otherwise a temporary file will be created.
        """
        args_text = " ".join(args)

        self.logfile = logfile
        self.logfile_choosen = logfile
        if self.logfile_choosen is not None:
            self.logfile_f = self.logfile_choosen.open("w")
        else:
            ntf = tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                delete_on_close=False,
            )
            self.logfile_choosen = pathlib.Path(ntf.name)
            assert isinstance(ntf.file, io.TextIOWrapper)
            self.logfile_f = ntf.file

        self._logging_info(f"EXEC {args_text}")
        self._logging_info(f"EXEC     cwd: {cwd}")

        self.proc = subprocess.Popen(  # pylint: disable=consider-using-with
            args=args,
            executable=executable,
            env=env,
            cwd=cwd,
            close_fds=False,
            text=True,
            stdout=self.logfile_f,
            stderr=subprocess.PIPE,
        )

    def _logging_info(self, msg: str) -> None:
        logger.info(msg)
        if self.logfile is not None:
            self.logfile_f.write(msg + "\n")

    def wait(self, timeout_s: float | None = None) -> int:
        rc = self.proc.wait(timeout=timeout_s)
        self._logging_info(f"EXEC rc:{rc}")

        if self.logfile is not None:
            self.logfile_f.close()
            stdout = self.logfile_choosen.read_text().strip()
            if stdout:
                logger.info(f"EXEC stdout:\n{stdout}")

        return rc


# def run_with_logging(
#     timeout_s: float | None = None,
# ) -> int:
#     """
#     Call sigrok binaries with
#     * specific env
#     * log output
#     """
#     try:
#         proc = subprocess.run(
#             executable=executable,
#             args=args,
#             env=env,
#             cwd=cwd,
#             timeout=timeout_s,
#             check=False,
#             capture_output=True,
#             text=True,
#         )
#     except subprocess.TimeoutExpired as e:
#         logger.info(f"EXEC {e!r}")
#         # logger.exception(e)
#         raise

#     logger.info(f"EXEC rc:{proc.returncode}")
#     stdout = proc.stdout.strip()
#     if stdout:
#         logger.info(f"EXEC stdout:\n{stdout}")
#     stderr = proc.stderr.strip()
#     if stderr:
#         logger.info(f"EXEC stderr:\n{stderr}")

#     return proc.returncode


def call_sigrok_cli(args: list[str]) -> None:
    popen = popen_appimage(APPIMAGE_SIGROK_CLI, args=args)
    rc = popen.wait()
    sys.exit(rc)


def call_pulseview(args: list[str]) -> None:
    popen = popen_appimage(APPIMAGE_PULSEVIEW, args=args)
    rc = popen.wait()
    sys.exit(rc)
