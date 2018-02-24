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
from datetime import datetime

import warnings

HEADERS = ["TeamID", "Time", "Packet", "Altitude", "Pressure", "Airspeed", "Temperature", "Voltage", "Latitude", "Longitude",
"GPSAlt", "Satellites", "GPSSpeed", "Heading", "ImageCount", "State"]


class Wrapper():

    def __init__(self, ui, xbee_communicator, dataloader=None):
        self.ui = ui
        self.ax = None
        self.xbee_communicator = xbee_communicator

        # populate plot select menu
        self.ui.comboBox.clear()
        self.ui.comboBox.addItem("All")
        # should create separate array of items we want to plot
        self.ui.comboBox.addItems(HEADERS)

        # store the current option select in plot select
        self.currentPlot = self.ui.comboBox.currentText()

        if dataloader:
            # Create default dataloader? Dataloader should be initialized with directory/file name
            self.dataloader = dataloader
            pass

    def codeUpdatesToUI(self):
        self.ui.figure = Figure()
        self.ui.canvas = FigureCanvas(ui.figure)
        self.ui.canvas.setObjectName("gridCanvas")
        self.ui.gridLayout.addWidget(ui.canvas, 0, 0, 1, 1)
        if self.dataloader is not None:
            self.update_session_name(self.dataloader.file_name)

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
        self.ui.canvas.draw()

    # plots new points 
    def plot_points(self, data, x, y):
        self.ax.plot(data[x].tail(2).astype(float), 
            data[y].tail(2).astype(float), color = "xkcd:teal")
        self.ui.canvas.draw()

    # Clear the plot
    def plotClear(self):
        self.ax.clear()
        self.ui.canvas.draw()

    # Update values below graph
    # dataType is Velocity, Altitude, Temp, etc
    # Pass in "all" to update all data types
    def updateValues(self, data, dataType):
        self.ui.label_11.setText(str(dataType))
        # self.ui.label_11 is Time
        # self.ui.label_9 is Altitude
        # self.ui.label_6 is Velocity
        # self.ui.label_5 is Wind Speed
        # self.ui.label_4 is Pressure

    # Connects buttons to given functions
    def setUpHandlers(self):
        self.ui.actionConnect.triggered.connect(self.select_port)
        self.ui.actionStart.triggered.connect(self.xbee_start)
        self.ui.actionPause.triggered.connect(self.xbee_pause)
        self.ui.actionStop.triggered.connect(self.xbee_stop)
		
        self.ui.comboBox.activated.connect(self.setComboBox)

        self.ui.actionNew_Session.triggered.connect(self.new_session)
        self.ui.actionLoad_Session.triggered.connect(self.load_session)

    # Starts a new session (new data file)
    def new_session(self):
        if self.yesno_prompt("New Session", "Are you sure you want to start a new session?"):
            if self.dataloader is not None:
                self.dataloader.save_as_csv()

            # Use current time as filename
            self.dataloader = DataLoader("./data/" + str(datetime.now()) + ".csv")
            self.dataloader.save_as_csv()
            self.update_session_name(self.dataloader.file_name)

            # Clear old plot and plot new data (which is nothing)
            self.plotClear()
            data = self.dataloader.fetch(["Time", "Altitude"])
            window.plot(data, "Time", "Altitude")

    # Loads a session from an old csv file
    def load_session(self):
        if self.yesno_prompt("Load Session", "Are you sure you want to load a session?"):

            # Prompt user to choose filename
            chosen = self.openFileNameDialog()
            if chosen == '':
                return

            # Save current data loader
            if self.dataloader is not None:
                self.dataloader.save_as_csv()
            
            # Load data from file
            self.dataloader = DataLoader(chosen)
            self.dataloader.read_file()
            self.update_session_name(self.dataloader.file_name)

            # Plot again - ideally migrate to an update UI function
            self.plotClear()
            data = self.dataloader.fetch(["Time", "Altitude"])
            window.plot(data, "Time", "Altitude")


    def select_port(self):
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
            self.warningdialog("Not connected; cannot start.")

    def xbee_pause(self):
        valid = xbee_communicator.start()
        if not valid:
            self.warningdialog("Not connected; cannot pause.")

    def xbee_stop(self):
        valid = xbee_communicator.start()
        if not valid:
            self.warningdialog("Not connected; cannot stop.")

    def inputdialog(self, title, message):
        return QtWidgets.QInputDialog.getText(self.ui.mainwindow, title, message)
		
    # update the current plot and replace the previous plot
    def setComboBox(self, index):
        self.currentPlot = self.ui.comboBox.itemText(index)
        
        if (self.currentPlot == "All"):
            pass
        else:
            data = self.dataloader.fetch(["Time", self.currentPlot])
            warnings.filterwarnings("ignore",module="matplotlib")
            self.plotClear()
            self.plot(data, "Time", self.currentPlot)
        
    def getCurrentPlot(self):
        return self.currentPlot

    def warningdialog(self, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(message)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setWindowTitle("WARNING!")
        ret = msg.exec_()

    def yesno_prompt(self, title, msg):
        reply = QtWidgets.QMessageBox.question(self.ui.mainwindow, title, 
                 msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            return True
        else:
            return False   

    def openFileNameDialog(self):    
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui.mainwindow,"QFileDialog.getOpenFileName()", 
            "","All Files (*);;Python Files (*.py)", options=options)
        return fileName

    def update_session_name(self, name):
        self.ui.session_label.setText(name)

# Instantiate UI
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    ui.mainwindow = MainWindow

    # Setup necessary components
    # Optional
    dataloader = DataLoader("./data/Data.txt")
    xbee_communicator = XBeeCommunicator()

    # Create wrapper around UI Window
    window = Wrapper(ui, xbee_communicator, dataloader)
    window.codeUpdatesToUI()
    window.setUpHandlers()

    # Create dataloader
    dataloader.read_file()
    data = dataloader.fetch(["Time", "Altitude"])
    window.plot(data, "Time", "Altitude")

    # Show window
    MainWindow.show()

    # Testing adding additional data points
    # print(data["Time"].tail(2), "\n", data["Altitude"].tail(2), "\n")
    dataloader.update(HEADERS, [randint(0, 300) for n in range(0, len(HEADERS))])

    data = dataloader.fetch(["Time", "Altitude"])
    # print(data["Time"].tail(2), "\n", data["Altitude"].tail(2))
    window.plot_points(data, "Time", "Altitude")

    # Create timer to change display of text
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: window.updateValues(data, randint(0, 10)))
    timer.start(1000)

    sys.exit(app.exec_())
