from octoprobe.usb_tentacle.usb_constants import HwVersion
from octoprobe.util_baseclasses import TentaclesCollector

from testbed_cb_jtag_probe.constants import TESTBED_NAME

from . import tentacle_specs

TENTACLES_INVENTORY = (
    TentaclesCollector(testbed_name=TESTBED_NAME).add_testbed_instance(
        testbed_instance="ch_hans_1",
        tentacles=[
            (
                "de6550358785-7421",
                HwVersion.V07,
                "v1.0",
                tentacle_specs.MCU_JTAGPROBE,
            ),
        ],
    )
).inventory
