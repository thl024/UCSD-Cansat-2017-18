import sys

from mainwindow import Ui_MainWindow
from dataloader import DataLoader
from xbee import XBeeCommunicator

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from random import randint

HEADERS = ["TeamID", "Time", "Packet", "Altitude", "Pressure", "Airspeed", "Temperature", "Voltage", "Latitude", "Longitude",
"GPSAlt", "Satellites", "GPSSpeed", "Heading", "ImageCount", "State"]


class Wrapper():

    def __init__(self, ui, xbee_communicator, dataloader=None):
        self.ui = ui
        self.xbee_communicator = xbee_communicator
        if not dataloader:
            # Create default dataloader? Dataloader should be initialized with directory/file name
            pass

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
        self.ui.actionConnect.triggered.connect(self.selectPort)
        self.ui.actionStart.triggered.connect(self.xbee_start)
        self.ui.actionPause.triggered.connect(xbee_communicator.pause)
        self.ui.actionStop.triggered.connect(xbee_communicator.stop)

    def selectPort(self):
        valid = False
        while not valid:
            port, choice = self.inputdialog("Port", "Input Port (/dev/tty or COM)")
            if not choice:
                print("None selected")
                return
            else:
                print("Chosen port: {}".format(port))
                valid = xbee_communicator.connect(port)
                if not valid:
                    self.warningdialog("Not a valid port, try again.")

    def xbee_start(self):
        valid = xbee_communicator.start()
        if not valid:
            self.warningdialog("No connection; cannot start.")

    def xbee_pause(self):
        valid = xbee_communicator.start()
        if not valid:
            self.warningdialog("No connection; cannot pause.")

    def xbee_stop(self):
        valid = xbee_communicator.start()
        if not valid:
            self.warningdialog("No connection; cannot stop.")

    def inputdialog(self, title, message):
        return QtWidgets.QInputDialog.getText(self.ui.mainwindow, title, message)

    def warningdialog(self, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(message)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setWindowTitle("WARNING!")
        ret = msg.exec_()

# Instantiate UI
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    ui.mainwindow = MainWindow

    # Setup necessary components
    # Optional
    dataloader = DataLoader("./Data.txt")
    xbee_communicator = XBeeCommunicator()

    # Create wrapper around UI Window
    window = Wrapper(ui, xbee_communicator, dataloader)
    window.codeUpdatesToUI()
    window.setUpHandlers()

    # Show window
    MainWindow.show()

    sys.exit(app.exec_())
