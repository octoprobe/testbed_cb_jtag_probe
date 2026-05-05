Introduction
============


.. toctree::
   :glob:
   :maxdepth: 4

   **


.. image:: /images/work-in-progress.svg
   :height: 200px
   :align: center


The software `cb_jtag_probe` is implemented on the PC and as firmware a RP2350.

Octoprobe is used to automate the software tests.

.. image:: /design/block_diagram.drawio.svg
   :height: 500px
   :align: center

Implementation of the Octoprobe Tentacles
---------------------------------------------

.. image:: /design/diagram_tentacle_probe.drawio.svg
   :height: 500px
   :align: center

Features
---------------------------------------------

sigrok
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 * testbed_cb_jtag_probe flash-logic-analyzer
     Download and install the firmware

 * testbed_cb_jtag_probe download-sigrok
     Download appimage for sigrok-cli and pulseview

 * Allow to write/maintain sigrok decoder
     See: src/testbed_cb_jtag_probe/sigrok_decoders/jtag_cb

 * Automatic capture using sigrok-cli during pytest

jtag probe
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 * testbed_cb_jtag_probe flash-jtag
     Download and install the firmware
