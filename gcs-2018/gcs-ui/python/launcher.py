import sys

from mainwindow import Ui_MainWindow
from dataloader import DataLoader

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


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

    def plot(self, data):
        x = data.ix[:,0]
        plt.plot()


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

    MainWindow.show()
    sys.exit(app.exec_())