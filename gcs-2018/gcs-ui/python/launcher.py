import sys

from mainwindow import Ui_MainWindow
from dataloader import DataLoader
from xbee import XBeeCommunicator

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from mpl_toolkits.mplot3d import Axes3D

from random import randint
from datetime import datetime

import warnings

HEADERS = ["TeamID", "Time", "Packet", "Altitude", "Pressure", "Airspeed", "Temperature", "Voltage", "Latitude", "Longitude",
"GPSAlt", "Satellites", "GPSSpeed", "Heading", "ImageCount", "State"]

# Values below graph
v1 = "Time"
v2 = "Altitude"
v3 = "GPSSpeed"
v4 = "Airspeed"
v5 = "Temperature"

# Values below graph - units
v1_u = "s"
v2_u = "m"
v3_u = "mph"
v4_u = "mph"
v5_u = "°F"


class Wrapper():

    def __init__(self, ui, xbee_communicator, dataloader=None):
        self.ui = ui
        self.ax = None
        self.xbee_communicator = xbee_communicator

        # reference to 3d plot
        self.plot3d = None

        # hold the smallest min and largest max limits for the y axis
        # this lets us know the highest or lowest we can scale the graph
        self.yLimits = [0, 0]
        self.xLimits = [0, 0]

        # hold the current min and max limits for the y axis
        # this keeps track of the values the sliders are at
        self.minY = 0
        self.maxY = 0
        self.minX = 0
        self.maxX = 0

        # populate plot select menu
        self.ui.comboBox.clear()
        # self.ui.comboBox.addItem("All")
        # should create separate array of items we want to plot
        self.ui.comboBox.addItems(HEADERS[2:])

        self.ui.horizontalSlider_2.setValue(100)
        self.ui.horizontalSlider_4.setValue(100)

        # store the current option select in plot select
        self.currentPlot = self.ui.comboBox.currentText()

        if dataloader:
            # Create default dataloader? Dataloader should be initialized with directory/file name
            self.dataloader = dataloader
            pass

    def codeUpdatesToUI(self):
        self.ui.figure = Figure()
        self.ui.canvas = FigureCanvas(self.ui.figure)
        self.ui.canvas.setObjectName("gridCanvas")
        # add the plot to the main layout
        self.ui.gridLayout.addWidget(self.ui.canvas, 0, 0, 1, 1)

        # add a plot to the sub layout
        self.ui.figure2 = Figure()
        self.ui.canvas2 = FigureCanvas(self.ui.figure2)
        self.ui.canvas2.setObjectName("gridCanvas2")
        self.ui.gridLayout_2.addWidget(self.ui.canvas2, 0, 0, 1, 1)

    def initNewUI(self):

        # Change session name
        if self.dataloader is not None:

            # Update session name
            self.update_session_name(self.dataloader.file_name)
            
            if self.ax is not None:
                # Clear old plot to plot new data
                self.plotClear()

            # Plot initial data
            data = self.dataloader.fetch(["Time", self.currentPlot])

            # Compute new limits
            self.compute_plot_limits(data)

            # Update limits
            self.update_plot_limits()

            # Update plot controls
            self.update_plot_controls(True)

            # Plot
            self.plot(data, "Time", self.currentPlot)

            # plot 3d
            self.plotOrientation(0, 0, 0, 0.2, -0.4, 1.8)

            # Update text vals
            self.update_text_vals()

        else:
            # Update session name
            self.update_session_name("No File Loaded")

    def compute_plot_limits(self, data):
        
        data = data.astype(float)

        if not data.empty:
            self.maxX = int(data["Time"].max())
            self.maxY = int(data[self.currentPlot].max()) + 1
            self.minX = int(data["Time"].min())
            self.minY = int(data[self.currentPlot].min()) + 1
        else:
            self.maxX = 10
            self.maxY = 10
            self.minX = 0
            self.minY = 0

    def update_plot_limits(self):
        axes = self.ui.figure.gca()
        axes.set_xlim([self.minX, self.maxX])
        axes.set_ylim([self.minY, self.maxY])
        self.ui.canvas.draw()

    def update_plot_controls(self, set_slider_max):

        minVals = [self.minX, self.minY]
        maxVals = [self.maxX, self.maxY]
        mintxtedits = [self.ui.textEdit, self.ui.textEdit_3]
        maxtxtedits = [self.ui.textEdit_2, self.ui.textEdit_4]
        minsliders = [self.ui.horizontalSlider_3, self.ui.horizontalSlider]
        maxsliders = [self.ui.horizontalSlider_4, self.ui.horizontalSlider_2]

        for minval, minte, minslider, maxval, maxte, maxslider in zip(minVals, mintxtedits, minsliders, maxVals, maxtxtedits, maxsliders):
            minte.setText(str(minval))
            maxte.setText(str(maxval))

            if set_slider_max:
                minslider.setMinimum(minval)
                minslider.setMaximum(maxval)
                maxslider.setMinimum(minval)
                maxslider.setMaximum(maxval)

            minslider.setValue(minval)
            maxslider.setValue(maxval)

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
        self.ax.set_title("{} vs {}".format(x, y))
        self.ax.set_xlabel(x)
        self.ax.set_ylabel(y)
        self.ax.grid()
        self.ui.canvas.draw()

    # plots new points 
    def plot_points(self, data, x, y):
        self.ax.plot(data[x].tail(2).astype(float), 
            data[y].tail(2).astype(float), color = "xkcd:teal")

        self.setXLimits()
        self.setYLimits()

        self.ui.canvas.draw()

    # Clear the plot
    def plotClear(self):
        self.ax.clear()
        self.ui.canvas.draw()

    # plots 3d
    # use u v w for orientation/direction of arrow
    # x y z is for initial position of tail
    def plotOrientation(self, x, y, z, u, v, w):
        ax = self.ui.figure2.add_subplot(111, projection = "3d")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.quiver(x, y, z, u, v, w)
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1.5])
        ax.set_zlim([-1, 2])
        self.ui.canvas2.draw()

    # Connects buttons to given functions
    def setUpHandlers(self):
        self.ui.actionConnect.triggered.connect(self.select_port)
        self.ui.actionStart.triggered.connect(self.xbee_start)
        self.ui.actionPause.triggered.connect(self.xbee_pause)
        self.ui.actionStop.triggered.connect(self.xbee_stop)
		
        # detect when a new plot has been selected
        self.ui.comboBox.activated.connect(self.setComboBox)

        # detect when max sliders have changed
        self.ui.horizontalSlider_2.valueChanged.connect(partial(self.maxSliderChange, self.ui.horizontalSlider_2)) # Y Max
        self.ui.horizontalSlider_4.valueChanged.connect(partial(self.maxSliderChange, self.ui.horizontalSlider_4)) # X Max

        # detect when min sliders have changed
        self.ui.horizontalSlider.valueChanged.connect(partial(self.minSliderChange, self.ui.horizontalSlider)) # Y Min
        self.ui.horizontalSlider_3.valueChanged.connect(partial(self.minSliderChange, self.ui.horizontalSlider_3)) # X Min

        self.ui.actionNew_Session.triggered.connect(self.new_session)
        self.ui.actionLoad_Session.triggered.connect(self.load_session)

        # Snapshot detection
        self.ui.pushButton.clicked.connect(self.snapshot)

    # Starts a new session (new data file)
    def new_session(self):
        if self.yesno_prompt("New Session", "Are you sure you want to start a new session?"):

            # Prompt user to choose filename
            fn = self.saveFileNameDialog()
            if fn == '':
                return

            # Save current data
            if self.dataloader is not None:
                self.dataloader.save_as_csv()

            # Use current time as filename
            self.dataloader = DataLoader(fn, HEADERS)
            self.dataloader.save_as_csv()

            self.initNewUI()

    # Loads a session from an old csv file
    def load_session(self):
        if self.yesno_prompt("Load Session", "Are you sure you want to load a session?"):

            # Prompt user to choose filename
            fn = self.openFileNameDialog()
            if fn == '':
                return

            # Save current data loader
            if self.dataloader is not None:
                self.dataloader.save_as_csv()
            
            # Load data from file
            self.dataloader = DataLoader(fn, HEADERS)
            self.dataloader.read_file()
            
            self.initNewUI()

    def xbee_update(self, data_row):
        if self.dataloader is None:
            print("Error: Session has not been started")
            return

        self.dataloader.update(HEADERS, data_row)

        x = "Time"
        y = self.currentPlot

        # Fetch data
        data = self.dataloader.fetch([x, y])
        
        # Compute new limits
        self.compute_plot_limits(data)

        # Update limits
        self.update_plot_limits()

        # Update plot controls
        self.update_plot_controls(True)

        print("here")

        # Update plot
        self.plot_points(data, x, y)

        # Update text below graph
        self.update_text_vals()

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
        valid = xbee_communicator.start(self.xbee_update)
        if not valid:
            self.warningdialog("Not connected; cannot start.")

    def xbee_pause(self):
        valid = xbee_communicator.pause()
        if not valid:
            self.warningdialog("Not connected; cannot pause.")

    def xbee_stop(self):
        valid = xbee_communicator.stop()
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

            # Compute new limits
            self.compute_plot_limits(data)

            # Update limits
            self.update_plot_limits()

            # Update plot controls
            self.update_plot_controls(True)

    # change the max range of the y axis using slider
    def maxSliderChange(self, slider):
        newMaxValue = slider.value()
        axes = self.ui.figure.gca()

        # slider for Y Max
        if (slider == self.ui.horizontalSlider_2):
            if self.minY < newMaxValue:
                self.maxY = newMaxValue
                self.update_plot_limits()
        # slider for X Max
        else:
            if self.minX < newMaxValue:
                self.maxX = newMaxValue
                self.update_plot_limits()
        warnings.filterwarnings("ignore",module="matplotlib")

        self.update_plot_controls(False)

    # change the min range of the y axis using slider
    def minSliderChange(self, slider):
        newMinValue = slider.value()
        axes = self.ui.figure.gca()

        # Slider for Y Min
        if (slider == self.ui.horizontalSlider):
            if newMinValue < self.maxY:
                self.minY = newMinValue
                self.update_plot_limits()
        # Slider for X Min
        else:
            if newMinValue < self.maxX:
                self.minX = newMinValue
                self.update_plot_limits()

        warnings.filterwarnings("ignore",module="matplotlib")
            
        self.update_plot_controls(False)
        
    def getCurrentPlot(self):
        return self.currentPlot

    def snapshot(self):
        if not self.xbee_communicator.snapshot():
            self.warningdialog("Not connected to XBee")

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
        return True if reply == QtWidgets.QMessageBox.Yes else False

    def openFileNameDialog(self):    
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui.mainwindow,"QFileDialog.getOpenFileName()", 
            "","All Files (*);;Python Files (*.py)", options=options)
        return fileName

    def saveFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self.ui.mainwindow,"QFileDialog.getSaveFileName()", 
            "","All Files (*);;Python Files (*.py)", options=options)
        return fileName

    def update_session_name(self, name):
        self.ui.session_label.setText(name)

    def update_text_vals(self):
        label_order = [self.ui.label_11, self.ui.label_9, self.ui.label_6, self.ui.label_5, self.ui.label_4]
        for field, unit, label in zip([v1, v2, v3, v4, v5], [v1_u, v2_u, v3_u, v4_u, v5_u], label_order):
            txt_data = self.dataloader.fetch([field])
            text = str(txt_data[field].iloc[-1]) + unit if len(txt_data[field]) > 1 else "N/A"
            label.setText(text)

# Instantiate UI
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    ui.mainwindow = MainWindow

    # Setup necessary components
    # Optional
    dataloader = DataLoader("./data/Data.txt", HEADERS)
    dataloader.read_file()

    xbee_communicator = XBeeCommunicator()

    # Create wrapper around UI Window
    window = Wrapper(ui, xbee_communicator, dataloader)
    window.codeUpdatesToUI()
    window.setUpHandlers()
    window.initNewUI()

    # Show window
    MainWindow.show()

    sys.exit(app.exec_())
