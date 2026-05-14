import logging
import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

logger = logging.getLogger(__file__)


def test_pyqtgraph() -> None:
    filename_capture = DIRECTORY_OF_THIS_FILE / "capture-gusmanb/capture.lac"
    assert filename_capture.exists()

    import sys

    import numpy as np
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)

    win = pg.GraphicsLayoutWidget(show=True)
    win.setWindowTitle("DAQ Scope")

    plot = win.addPlot()
    plot.showGrid(x=True, y=True)

    curve = plot.plot(pen="y")

    # Fake DAQ signal
    x = np.linspace(0, 1, 5000)
    y = np.sin(2 * np.pi * 50 * x)

    curve.setData(x, y)

    # Dark oscilloscope theme
    pg.setConfigOption("background", "k")
    pg.setConfigOption("foreground", "g")

    # Export PNG
    from pyqtgraph.exporters import ImageExporter

    exporter = ImageExporter(plot)
    exporter.export("capture.png")

    # Keep test non-interactive: do not terminate pytest via sys.exit().
    app.quit()
