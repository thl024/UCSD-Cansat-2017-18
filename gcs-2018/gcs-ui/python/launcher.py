import sys

from mainwindow import Ui_MainWindow
from dataloader import DataLoader

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from random import randint

HEADERS = ["TeamID", "Time", "Packet", "Altitude", "Pressure", "Airspeed", "Temperature", "Voltage", "Latitude", "Longitude",
"GPSAlt", "Satellites", "GPSSpeed", "Heading", "ImageCount", "State"]


class WindowWrapper():

    def __init__(self, ui):
        self.ui = ui


    def codeUpdatesToUI(self):
        self.ui.figure = Figure()
        self.ui.canvas = FigureCanvas(ui.figure)
        self.ui.canvas.setObjectName("gridCanvas")
        self.ui.gridLayout.addWidget(ui.canvas, 0, 0, 1, 1)

    # plot the data
    """
    need to use data.astype(float) so it can process the data
    need ax = self.ui.figure.add_subplot(111) to show the graph
    set x axis to Time and y axis to altitude
    """
    def plot(self, data):
        x = data.ix[:,0]
        data.astype(float).plot(ax = self.ui.figure.add_subplot(111),
            x = "Time", y = "Altitude")


    def setUpHandlers(self):
        pass

# Instantiate UI
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    # Create wrapper around UI Window
    window = WindowWrapper(ui)
    window.codeUpdatesToUI()

    # Create dataloader
    dataloader = DataLoader("./Data.txt")
    dataloader.read_file()
    data = dataloader.fetch(["Time", "Altitude"])
    window.plot(data)

    # Show window
    MainWindow.show()

    # Test update
    dataloader.update(HEADERS, [randint(0, 300) for n in range(0, len(HEADERS))])

    sys.exit(app.exec_())
