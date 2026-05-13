from __future__ import annotations

import logging
import pathlib
import typing

import typer
from mpremote.transport_serial import TransportError
from octoprobe.scripts import op_flash
from octoprobe.scripts.op import (
    PoweronAnnotation,
    SerialsAnnotation,
    iter_usb_tentacles,
)
from octoprobe.scripts.op_logging import init_logging
from octoprobe.util_baseclasses import OctoprobeAppExitException
from octoprobe.util_pyudev import UdevPoller
from octoprobe.util_tentacle_label import label_renderer

from .. import constants, tentacle_spec, util_sigrok
from ..tentacles_inventory import TENTACLES_INVENTORY

logger = logging.getLogger(__file__)

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer()


@app.command()
def labels() -> None:
    init_logging()

    filename = constants.DIRECTORY_DOWNLOADS / "testbed_labels.pdf"
    label_renderer.create_report(
        filename=filename,
        layout=label_renderer.RendererLabelBolzoneDuo(),
        labels=TENTACLES_INVENTORY.labels_data,
    )
    print(f"Created: {filename}")


@app.command(help="Download appimage sigrok-cli and pulseview")
def download_sigrok(
    url_base: str = "https://github.com/hmaerki/fork_sigrok-build/releases/download/continuous",
) -> None:
    init_logging()

    util_sigrok.download_sigrok(url_base=url_base)


@app.command(
    help="Call sigrok-cli",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def sigrok_cli(ctx: typer.Context) -> None:
    init_logging()

    util_sigrok.call_sigrok_cli(args=ctx.args)


@app.command(
    help="Call pulseview",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def pulseview(ctx: typer.Context) -> None:
    init_logging()

    util_sigrok.call_pulseview(args=ctx.args)


@app.command(help="Flash cb_jtag_probe.")
def flash_jtag(
    firmware_url: str = "https://github.com/chriesibaum/cb_jtag_probe_fw/releases/download/v0.2.3/cb_jtag_probe_v0.2.3-0-gf3f6a18_rpi_pico2_rp2350a_m33.uf2",
    serials: SerialsAnnotation = None,
    poweron: PoweronAnnotation = False,
) -> None:
    init_logging()

    with UdevPoller() as udev:
        for usb_tentacle in iter_usb_tentacles(poweron=poweron, serials=serials):
            directory_logs = pathlib.Path("/tmp/testbed_cb_jtag_probe")
            tentacle = tentacle_spec.TentacleJTAG.factory_usb_tentacle(
                usb_tentacle=usb_tentacle
            )
            try:
                tentacle.infra.load_base_code_if_needed()
            except (TransportError, OctoprobeAppExitException):
                continue

            directory_logs = pathlib.Path("/tmp/heatguard")
            tentacle.flash_dut_picotool(
                udev=udev,
                firmware_url=firmware_url,
                directory_logs=directory_logs,
            )


@app.command(help="Flash pico_probe with ula (Micro Logic Analyzer).")
def flash_logic_analyzer(
    # firmware_url: str = "https://github.com/dotcypress/ula/releases/download/0.0.5/ula_0.0.5_generic.uf2",
    # firmware_url: str = str(
    #     constants.DIRECTORY_DOWNLOADS
    #     / "sigrok-gusmanb/logic-analyzer-firmware_v6.0.0_BOARD_PICO.uf2"
    # ),
    firmware_url: str = "https://github.com/pico-coder/sigrok-pico/raw/refs/heads/main/pico_sdk_sigrok/release/pico_original.uf2",
    serials: SerialsAnnotation = None,
    poweron: PoweronAnnotation = False,
) -> None:
    init_logging()

    for usb_tentacle in iter_usb_tentacles(poweron=poweron, serials=serials):
        op_flash.do_flash(
            usb_tentacle=usb_tentacle,
            is_infra=False,
            firmware_url=firmware_url,
        )


if __name__ == "__main__":
    app()
