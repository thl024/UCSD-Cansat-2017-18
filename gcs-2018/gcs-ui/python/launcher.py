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
        self.ax = None

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
    def plot(self, data, x, y):
        self.ax = self.ui.figure.add_subplot(111)
        self.ax.plot(data[x].astype(float), data[y].astype(float),
            color = "xkcd:teal")

    # plots new points 
    def plot_points(self, data, x, y):
        self.ax.plot(data[x].tail(2).astype(float), 
            data[y].tail(2).astype(float), color = "xkcd:teal")
        self.ui.canvas.draw()


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
    window.plot(data, "Time", "Altitude")

    MainWindow.show()

    print(data["Time"].tail(2), "\n", data["Altitude"].tail(2), "\n")
    dataloader.update(HEADERS, [randint(0, 300) for n in range(0, len(HEADERS))])

    data = dataloader.fetch(["Time", "Altitude"])
    print(data["Time"].tail(2), "\n", data["Altitude"].tail(2))
    window.plot_points(data, "Time", "Altitude")

    sys.exit(app.exec_())
