from PyQt4 import QtCore, QtGui, QtCore
from PyQt4.QtGui import *
import multiprocessing
# import Vector
import time
import serial
import operator
from multiprocessing import Queue as Q
import Queue
from multiprocessing import Process
import random
from functools import partial
import pyqtgraph as pg
import numpy as np
import pyqtgraph.opengl as gl
import pyqtgraph.exporters
import math
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

ALTITUDE_COLOR = "#B0171F"
PRESSURE_COLOR = "#9400D3"
TEMPERATURE_COLOR = "#473C8B"
SPEED_COLOR = "#4169E1"
VOLTAGE_COLOR = "#00688B"
GPSSPD_COLOR = "#008080"

BACKGROUND = "#000000"
PLOT_BACKGROUND = "#EBEBEB"
SYMBOL_PEN = "#000000"
BORDER_PEN = "#000000"
LABEL_COLOR = "#FFFFFF"

IMG_TIMEOUT = 30
JPG_NAME = "recieved.jpg"
CAM_CMD = "c\n"
RELEASE_CMD = "r\n"
TEAM_ID = ""  # Make sure this is set to the first field or no data will be logged.
SERIAL_LOG_NAME = "Data.txt"
DEFAULT_HEADER = "TeamID, Time, Packet, Altitude, Pressure, Airspeed, Temperature, Voltage, Latitude, " \
                 "Longitude, GPSAlt, Satellites, ImageTime, ImageCount\r\n"
AXIS_PEN = "#000000"

serialDataQ = Q()
serialStateQ = Q()
serialSendQ = Q()

GraphParam = ""
SetAxis = False
SerialCommsStatus = "Stop Serial"
SerialThreadStart = False

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


## note any multiprocessing code needs to be top-level to work on windows. Has something to do with pickling
## object methods. Object methods are not pickled in windows.df


def processstart(method, args, joining):
    # args needs to be a tuple.
    p = Process(target=method, args=args)
    p.daemon = True
    p.start()
    if (joining):
        p.join()


def logger(filename, queue):
    print("Logger process starting...")
    while (True):
        try:
            data = queue.get(0)
            print(data)
            f = open(filename, mode='a+')
            f.write(data)
            f.close()
            print(data)
        except Queue.Empty:
            pass
    print("Logger process end.")


def randomDataGen(filename="RandomData.txt", columns=14, timecol=2):
    t = 0
    while (True):

        f = open(filename, "a+")
        for i in range(columns):
            if i is not timecol - 1:
                f.write(str(random.randrange(0, 100, 1)))
                if (i < columns - 1):
                    f.write(",")
                else:
                    f.write("\n")
            else:
                f.write(str(t*1000))
                if (i < columns - 1):
                    f.write(",")
                else:
                    f.write("\n")

        t += 1
        f.close()
        time.sleep(1)


## end of multiprocessing code
##--------------------------------------------------------------------------------------------------------------


class Ui_MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(Ui_MainWindow, self).__init__(parent)
        self.showplot = ""  # front
        self.colors = self.parsecolors()  # front
        self.actionsView = []  # front
        self.data = self.fileparse(SERIAL_LOG_NAME)  # back
        self.plots = []

        self.PortSet = False
        self.scroll = True

        # self.plainTextEditTerm.setStyleSheet("color:black; background-color:white")
        # self.tabWidgetPlot.setStyleSheet('QTabWidget>QWidget>QWidget{background: '+BACKGROUND+';}')

    def begin(self):
        self.setupUi()
        self.show()
        self.iniview()
        self.graphicsView.setBackground(PLOT_BACKGROUND)
        self.graphicsView.ci.setBorder(BORDER_PEN)
        self.plainTextEditTerm.setEnabled(False)
        self.warningdialog("Enter a Port to Start Serial comms")

    def setupUi(self):
        self.setObjectName(_fromUtf8("MainWindow"))
        self.resize(1234, 877)
        self.centralwidget = QtGui.QWidget(self)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tabWidgetPlot = QtGui.QTabWidget(self.centralwidget)
        self.tabWidgetPlot.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.tabWidgetPlot.setObjectName(_fromUtf8("tabWidgetPlot"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.gridLayout_2 = QtGui.QVBoxLayout(self.tab)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        # Plot widget
        self.graphicsView = pg.GraphicsLayoutWidget(self.tab)
        self.graphicsView.setObjectName(_fromUtf8("graphicsView"))
        self.gridLayout_2.addWidget(self.graphicsView)
        self.tabWidgetPlot.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))

        # self.gridwidget_pic = QtGui.QWidget(self.tab_2)
        self.gridLayout_pic = QtGui.QGridLayout(self.tab_2)
        self.gridLayout_pic.setObjectName(_fromUtf8("gridLayout_pic"))
        self.imgView = QtGui.QLabel()
        self.imgView.setObjectName(_fromUtf8("imgView"))
        self.imgView.setAlignment(QtCore.Qt.AlignCenter)
        self.imgScrollArea = QtGui.QScrollArea(self.tab_2)
        self.imgScrollArea.setWidget(self.imgView)
        self.gridLayout_pic.addWidget(self.imgScrollArea)
        # Picture

        # self.gridLayout_pic.addWidget(self.imgView)
        self.imgScrollArea.setWidgetResizable(True)

        self.tabWidgetPlot.addTab(self.tab_2, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidgetPlot, 3, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1234, 26))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuSerial = QtGui.QMenu(self.menubar)
        self.menuSerial.setObjectName(_fromUtf8("menuSerial"))
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName(_fromUtf8("menuView"))
        self.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        self.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(self)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

        self.dockWidgetCommand = QtGui.QDockWidget(self)
        self.dockWidgetCommand.setObjectName(_fromUtf8("dockWidgetCommand"))
        self.dockWidgetContents_4 = QtGui.QWidget()
        self.dockWidgetContents_4.setObjectName(_fromUtf8("dockWidgetContents_4"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents_4)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBoxCommand = QtGui.QGroupBox(self.dockWidgetContents_4)
        self.groupBoxCommand.setObjectName(_fromUtf8("groupBoxCommand"))
        self.gridLayout_7 = QtGui.QGridLayout(self.groupBoxCommand)
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.gridLayoutCommand = QtGui.QGridLayout()
        self.gridLayoutCommand.setObjectName(_fromUtf8("gridLayoutCommand"))
        self.pushButtonExtra = QtGui.QPushButton(self.groupBoxCommand)
        self.pushButtonExtra.setObjectName(_fromUtf8("pushButtonExtra"))
        self.gridLayoutCommand.addWidget(self.pushButtonExtra, 1, 0, 1, 1)
        # Camera button
        self.pushButtonCam = QtGui.QPushButton(self.groupBoxCommand)
        self.pushButtonCam.setObjectName(_fromUtf8("pushButtonCam"))

        self.gridLayoutCommand.addWidget(self.pushButtonCam, 0, 0, 1, 1)
        # Release Button
        self.pushButtonRelease = QtGui.QPushButton(self.groupBoxCommand)
        self.pushButtonRelease.setObjectName(_fromUtf8("pushButtonRelease"))

        self.gridLayoutCommand.addWidget(self.pushButtonRelease, 0, 1, 1, 1)
        self.pushButtonExtra_2 = QtGui.QPushButton(self.groupBoxCommand)
        self.pushButtonExtra_2.setObjectName(_fromUtf8("pushButtonExtra_2"))
        self.gridLayoutCommand.addWidget(self.pushButtonExtra_2, 1, 1, 1, 1)
        self.gridLayout_7.addLayout(self.gridLayoutCommand, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBoxCommand)
        self.groupBoxParam = QtGui.QGroupBox(self.dockWidgetContents_4)
        self.groupBoxParam.setObjectName(_fromUtf8("groupBoxParam"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBoxParam)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.gridLayoutSend = QtGui.QGridLayout()
        self.gridLayoutSend.setObjectName(_fromUtf8("gridLayoutSend"))
        # img command
        self.groupBoxImage = QtGui.QGroupBox(self.dockWidgetContents_4)
        self.groupBoxImage.setObjectName(_fromUtf8("groupBoxImage"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBoxImage)
        self.pushButtonImg = QtGui.QPushButton()
        self.verticalLayout_3.addWidget(self.pushButtonImg)
        # Entry for parameters
        self.lineEditParam = QtGui.QLineEdit(self.groupBoxParam)
        self.lineEditParam.setObjectName(_fromUtf8("lineEditParam"))

        self.gridLayoutSend.addWidget(self.lineEditParam, 0, 1, 1, 1)
        # Param Send button
        self.pushButtonParam = QtGui.QPushButton(self.groupBoxParam)
        self.pushButtonParam.setObjectName(_fromUtf8("pushButtonParam"))

        self.gridLayoutSend.addWidget(self.pushButtonParam, 0, 0, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayoutSend)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.verticalLayout.addWidget(self.groupBoxImage)
        self.verticalLayout.addWidget(self.groupBoxParam)

        self.dockWidgetCommand.setWidget(self.dockWidgetContents_4)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.dockWidgetCommand)
        self.dockWidgetTerm = QtGui.QDockWidget(self)
        self.dockWidgetTerm.setObjectName(_fromUtf8("dockWidgetTerm"))
        self.dockWidgetContents_6 = QtGui.QWidget()
        self.dockWidgetContents_6.setObjectName(_fromUtf8("dockWidgetContents_6"))
        self.gridLayout_4 = QtGui.QGridLayout(self.dockWidgetContents_6)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.verticalLayoutTerm = QtGui.QVBoxLayout()
        self.verticalLayoutTerm.setObjectName(_fromUtf8("verticalLayoutTerm"))

        # Button for pausing the terminal
        self.toolButtonPauseTerm = QtGui.QToolButton(self.dockWidgetContents_6)
        self.toolButtonPauseTerm.setObjectName(_fromUtf8("toolButtonPauseTerm"))

        self.verticalLayoutTerm.addWidget(self.toolButtonPauseTerm)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayoutTerm.addItem(spacerItem1)
        self.gridLayout_4.addLayout(self.verticalLayoutTerm, 0, 1, 1, 1)

        # Terminal text box
        self.plainTextEditTerm = QtGui.QPlainTextEdit(self.dockWidgetContents_6)
        self.plainTextEditTerm.setObjectName(_fromUtf8("plainTextEditTerm"))

        self.gridLayout_4.addWidget(self.plainTextEditTerm, 0, 0, 1, 1)
        self.dockWidgetTerm.setWidget(self.dockWidgetContents_6)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(8), self.dockWidgetTerm)
        self.dockWidgetPlotControl = QtGui.QDockWidget(self)
        self.dockWidgetPlotControl.setObjectName(_fromUtf8("dockWidgetPlotControl"))
        self.dockWidgetContents_7 = QtGui.QWidget()
        self.dockWidgetContents_7.setObjectName(_fromUtf8("dockWidgetContents_7"))
        self.gridLayout_8 = QtGui.QGridLayout(self.dockWidgetContents_7)
        self.gridLayout_8.setObjectName(_fromUtf8("gridLayout_8"))
        self.groupBoxPlotControl = QtGui.QGroupBox(self.dockWidgetContents_7)
        self.groupBoxPlotControl.setObjectName(_fromUtf8("groupBoxPlotControl"))
        self.gridLayout_9 = QtGui.QGridLayout(self.groupBoxPlotControl)
        self.gridLayout_9.setObjectName(_fromUtf8("gridLayout_9"))
        self.horizontalLayoutControls_3 = QtGui.QHBoxLayout()
        self.horizontalLayoutControls_3.setObjectName(_fromUtf8("horizontalLayoutControls_3"))

        # #-------------------------------------------
        self.GLWidget = gl.GLViewWidget()
        self.dockWidgetOpenGL = QtGui.QDockWidget(self)
        self.dockWidgetOpenGL.setWidget(self.GLWidget)
        self.dockWidgetOpenGL.setObjectName(_fromUtf8("dockWidgetOpenGL"))
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.dockWidgetOpenGL)

        # #-------------------------------------------
        # Spin box for choosing how many points to display IRT
        self.spinBoxPoints = QtGui.QSpinBox(self.groupBoxPlotControl)
        self.spinBoxPoints.setObjectName(_fromUtf8("spinBoxPoints"))

        self.horizontalLayoutControls_3.addWidget(self.spinBoxPoints)

        # Button for setting the current spinbox value
        self.pushButtonSetPoints = QtGui.QPushButton(self.groupBoxPlotControl)
        self.pushButtonSetPoints.setObjectName(_fromUtf8("pushButtonSetPoints"))

        self.horizontalLayoutControls_3.addWidget(self.pushButtonSetPoints)
        self.gridLayout_9.addLayout(self.horizontalLayoutControls_3, 7, 0, 1, 1)
        self.horizontalLayoutControls_2 = QtGui.QHBoxLayout()
        self.horizontalLayoutControls_2.setObjectName(_fromUtf8("horizontalLayoutControls_2"))

        # Max slider
        self.horizontalSliderMax = QtGui.QSlider(self.groupBoxPlotControl)
        self.horizontalSliderMax.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSliderMax.setObjectName(_fromUtf8("horizontalSliderMax"))
        self.horizontalLayoutControls_2.addWidget(self.horizontalSliderMax)

        # Text input for Max range value
        self.lineEditMax = QtGui.QLineEdit(self.groupBoxPlotControl)
        self.lineEditMax.setObjectName(_fromUtf8("lineEditMax"))

        self.horizontalLayoutControls_2.addWidget(self.lineEditMax)
        self.gridLayout_9.addLayout(self.horizontalLayoutControls_2, 4, 0, 1, 1)

        # Button for setting text input for Max Range
        self.pushButtonSetRange = QtGui.QPushButton(self.groupBoxPlotControl)
        self.pushButtonSetRange.setObjectName(_fromUtf8("pushButtonSetRange"))

        self.gridLayout_9.addWidget(self.pushButtonSetRange, 5, 0, 1, 1)
        self.labelMax = QtGui.QLabel(self.groupBoxPlotControl)
        self.labelMax.setObjectName(_fromUtf8("labelMax"))
        self.gridLayout_9.addWidget(self.labelMax, 3, 0, 1, 1)
        self.labelMin = QtGui.QLabel(self.groupBoxPlotControl)
        self.labelMin.setObjectName(_fromUtf8("labelMin"))
        self.gridLayout_9.addWidget(self.labelMin, 0, 0, 1, 1)
        self.horizontalLayoutControls = QtGui.QHBoxLayout()
        self.horizontalLayoutControls.setObjectName(_fromUtf8("horizontalLayoutControls"))

        # Slider for minimum value
        self.horizontalSliderMin = QtGui.QSlider(self.groupBoxPlotControl)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.horizontalSliderMin.sizePolicy().hasHeightForWidth())
        self.horizontalSliderMin.setSizePolicy(sizePolicy)
        self.horizontalSliderMin.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSliderMin.setObjectName(_fromUtf8("horizontalSliderMin"))
        self.horizontalLayoutControls.addWidget(self.horizontalSliderMin)

        # Min range text entry
        self.lineEditMin = QtGui.QLineEdit(self.groupBoxPlotControl)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEditMin.sizePolicy().hasHeightForWidth())
        self.lineEditMin.setSizePolicy(sizePolicy)
        self.lineEditMin.setObjectName(_fromUtf8("lineEditMin"))
        self.horizontalLayoutControls.addWidget(self.lineEditMin)
        self.gridLayout_9.addLayout(self.horizontalLayoutControls, 1, 0, 1, 1)
        self.labelPoints = QtGui.QLabel(self.groupBoxPlotControl)
        self.labelPoints.setObjectName(_fromUtf8("labelPoints"))
        self.gridLayout_9.addWidget(self.labelPoints, 6, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_9.addItem(spacerItem2, 8, 0, 1, 1)
        self.gridLayout_8.addWidget(self.groupBoxPlotControl, 0, 0, 1, 1)
        self.dockWidgetPlotControl.setWidget(self.dockWidgetContents_7)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.dockWidgetPlotControl)
        self.actionExit = QtGui.QAction(self)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionSave_Figure = QtGui.QAction(self)
        self.actionSave_Figure.setObjectName(_fromUtf8("actionSave_Figure"))
        self.actionPort = QtGui.QAction(self)
        self.actionPort.setObjectName(_fromUtf8("actionPort"))
        self.actionStart_Comms = QtGui.QAction(self)
        self.actionStart_Comms.setObjectName(_fromUtf8("actionStart_Comms"))
        self.actionPause_Comms = QtGui.QAction(self)
        self.actionPause_Comms.setObjectName(_fromUtf8("actionPause_Comms"))
        self.actionEnd_Comms = QtGui.QAction(self)
        self.actionEnd_Comms.setObjectName(_fromUtf8("actionEnd_Comms"))
        self.menuFile.addAction(self.actionSave_Figure)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuSerial.addAction(self.actionPort)
        self.menuSerial.addSeparator()
        self.menuSerial.addAction(self.actionStart_Comms)
        self.menuSerial.addAction(self.actionPause_Comms)
        self.menuSerial.addSeparator()
        self.menuSerial.addAction(self.actionEnd_Comms)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuSerial.menuAction())
        self.menubar.addAction(self.menuView.menuAction())

        self.retranslateUi()
        self.tabWidgetPlot.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        self.setWindowTitle(_translate("MainWindow", "qtGCS 1.0 Beta", None))
        self.tabWidgetPlot.setTabText(self.tabWidgetPlot.indexOf(self.tab), _translate("MainWindow", "Plot", None))
        # self.imgView.setText(_translate("MainWindow", "Picture Label", None))
        self.tabWidgetPlot.setTabText(self.tabWidgetPlot.indexOf(self.tab_2), _translate("MainWindow", "Image", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuSerial.setTitle(_translate("MainWindow", "Serial", None))
        self.menuView.setTitle(_translate("MainWindow", "View", None))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar", None))
        self.dockWidgetCommand.setWindowTitle(_translate("MainWindow", "Command", None))
        self.groupBoxCommand.setTitle(_translate("MainWindow", "Quick Commands", None))
        self.pushButtonExtra.setText(_translate("MainWindow", "Extra 1", None))
        self.pushButtonCam.setText(_translate("MainWindow", "Snapshot", None))
        self.pushButtonRelease.setText(_translate("MainWindow", "Release", None))
        self.pushButtonExtra_2.setText(_translate("MainWindow", "Extra 2", None))
        self.groupBoxParam.setTitle(_translate("MainWindow", "Param Send", None))
        self.groupBoxImage.setTitle(_translate("MainWindow", "Image", None))
        self.pushButtonParam.setText(_translate("MainWindow", "Send", None))
        self.dockWidgetTerm.setWindowTitle(_translate("MainWindow", "Terminal Out", None))
        self.toolButtonPauseTerm.setText(_translate("MainWindow", "...", None))
        self.dockWidgetPlotControl.setWindowTitle(_translate("MainWindow", "Plot Control", None))
        self.dockWidgetOpenGL.setWindowTitle(_translate("MainWindow", "OpenGL", None))
        self.groupBoxPlotControl.setTitle(_translate("MainWindow", "Plot Controls", None))
        self.pushButtonSetPoints.setText(_translate("MainWindow", "Set", None))
        self.pushButtonSetRange.setText(_translate("MainWindow", "Set", None))
        self.labelMax.setText(_translate("MainWindow", "Max:", None))
        self.labelMin.setText(_translate("MainWindow", "Min:", None))
        self.labelPoints.setText(_translate("MainWindow", "Points:", None))
        self.actionExit.setText(_translate("MainWindow", "Exit", None))
        self.actionSave_Figure.setText(_translate("MainWindow", "Save Figure", None))
        self.actionPort.setText(_translate("MainWindow", "Port", None))
        self.actionStart_Comms.setText(_translate("MainWindow", "Start Comms", None))
        self.actionPause_Comms.setText(_translate("MainWindow", "Pause Comms", None))
        self.actionEnd_Comms.setText(_translate("MainWindow", "End Comms", None))
        self.pushButtonImg.setText(_translate("MainWindow", "Load Image", None))

    def iniview(self):
        for i, list in enumerate(self.data):
            if list[0] == "Time" or list[0] == "time":  # get xaxis values column
                self.timeCol = i
            # add to menu
            self.actionsView.append(QtGui.QAction(self))
            self.actionsView[i].setText(_translate("MainWindow", list[0], None))
            self.menuView.addAction(self.actionsView[i])
            self.plots.append(plotObjs(list[0], self.colors[random.randrange(0, len(self.colors), 1)]))
            self.actionsView[i].triggered.connect(partial(self.changedisplay, self.plots[i].name))
        self.actionViewAll = QtGui.QAction(self)
        self.actionViewAll.setText(_translate("MainWindow", "All", None))
        self.menuView.addAction(self.actionViewAll)
        self.actionViewAll.triggered.connect(partial(self.changedisplay, "All"))

    def inibuttons(self):
        pass

    def saveFigure(self):
        pass

    def changedisplay(self, WhatDisp):
        # method that changes the displayed plot on the graph frame
        global GraphParam
        GraphParam = WhatDisp
        print("changing to: " + str(GraphParam))
        B.plotloop()

    def serialcontrol(self):
        global SerialCommsStatus

        if self.PortSet == False:
            pass

    def SendPacket(self, packet):
        if (serialSendQ.empty() == True):
            serialSendQ.put(packet, 0)
        else:
            self.warningdialog("Still sending previous packet!")

    def warningdialog(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setWindowTitle("WARNING!")
        ret = msg.exec_()

    def inputdialog(self, title, message):
        text, choice = QInputDialog.getText(self, title, message)
        print("You inputted: " + text)
        return text, choice

    def parsecolors(self):
        default = ["#B0171F", "#9400D3", "#473C8B", "#4169E1", "#00688B", "#008080"]
        try:
            f = open("colors.cfg", "r")
            data = f.read()
            list = data.split("\n")
            counter = 0
            while (True):
                counterprev = counter
                for i, val in enumerate(list):
                    if val == "":
                        counter += 1
                        list.remove(val)
                if (counterprev == counter):
                    break

            f.close()
            return list
        except:
            return default

    def choosecolorsrand(self, list):
        randlist = []
        index = []
        for i in range(len(list)):
            index.append(i)
        if (len(list) >= len(self.data)):
            for i, col in enumerate(self.data):
                randidx = random.choice(index)
                randlist.append(list[randidx])
                index.remove(randidx)

    def fileparse(self, log):
        try:
            fo2 = open(log, "r")
        except:
            fo2 = open(log, "a+")
            fo2.write(DEFAULT_HEADER)
        getData = fo2.read()
        fo2.close()
        lines = getData.split('\n')
        # print(lines)
        # Headers = parse_serial(lines[0])
        Headers = lines[0].split(",")
        # print(Headers)
        data = []
        for i, header in enumerate(Headers):
            # poplates data list with lists
            data.append([])
        # print(repr(data))
        for i, line in enumerate(lines):
            if (len(Headers) == len(line.split(","))):
                # print(repr(line))
                # dataPoints = parse_serial(line)
                dataPoints = line.split(",")
                # print(dataPoints)
                # populates dataPoints with values in each line
                for j, list in enumerate(data):
                    # populates sublists of each header with corresponding points of data.(2D array kinda)
                    data[j - 1].append(dataPoints[j - 1])
                    # print(data)
                    # #######-------------------########## working here.q
        return data








class Backend():
    def __init__(self, ui):
        # super(Backend, self).__init__()
        self.ui = ui
        self.iniserial()
        self.inicommand()
        self.inifilemmenu()
        global GraphParam
        GraphParam = ui.plots[0].name
        processstart(logger, (SERIAL_LOG_NAME, serialDataQ,), False)  # back
        #processstart(randomDataGen, (SERIAL_LOG_NAME, 16), False)
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(partial(self.plotloop))
        self.timer.start(500)
        self.logName = "Data.txt"  # back
        self.timeCol = ui.timeCol  # back
        self.data = ui.fileparse(SERIAL_LOG_NAME)  # back
        self.plotLoad = False  # back
        self.serialCommsIndicator = "End Serial"  # back
        self.threadStart = False  # back # back
        self.multiplot = []  # back
        self.port = ""  # back
        self.ran = False  # back
        self.ran2 = False  # back
        self.runIterator = 0  # back
        self.plots = ui.plots
        self.symbol = 'o'
        self.minrange = 0  # back
        self.maxrange = 0  # back
        self.displaypoints = 0  # back
        self.fileparse = ui.fileparse
        self.imgPathSet = False  # back
        self.imgPath = ""  # back
        self.plotobj = 0

    def plotloop(self):
        self.data = self.fileparse(SERIAL_LOG_NAME)
        # print(self.data)
        if GraphParam is not "All":
            if not self.ran2:
                self.ran2 = True
                ui.graphicsView.clear()
                self.plotobj = self.ui.graphicsView.addPlot()
                self.ran2 = True
                self.plotobj.showGrid(True, True, alpha=1)
                ax = self.plotobj.getAxis("bottom")
                ax.setPen(AXIS_PEN)
                ax = self.plotobj.getAxis("left")
                ax.setPen(AXIS_PEN)
            for i, list in enumerate(self.data):
                if GraphParam == list[0]:
                    self.plotobj.plot(np.array(self.data[self.timeCol][1:]).astype(np.float),
                                      np.array(list[1:]).astype(np.float),
                                      clear=True,
                                      title=self.plots[i].name,
                                      pen=self.plots[i].color,
                                      symbol=self.symbol,
                                      symbolPen=SYMBOL_PEN,
                                      symbolBrush=self.plots[i].color)
                    self.plotobj.setTitle(self.plots[i].name, color=self.plots[i].color)
                    # Set axis limits
                    self.setxaxis(self.plotobj)
            self.ran = False
        elif GraphParam == "All":
            if not self.ran:
                self.ran = True
                self.ui.graphicsView.clear()
                self.multiplot = []
                y = 0
                numlist = len(self.plots)
                for i, list in enumerate(self.data):
                    y = int(math.ceil(math.sqrt(numlist)))
                    x = int(math.ceil(float(numlist - y) / float(y))) + 1
                j = 0
                for i in range(numlist):
                    k = i % y
                    temp = self.ui.graphicsView.addPlot(row=j, col=k, rowspan=1, colspan=1)
                    self.multiplot.append(temp)
                    if (k == (y - 1)):
                        j += 1
                    self.multiplot[i].showGrid(True, True, alpha=1)
                    ax1 = self.multiplot[i].getAxis("left")
                    ax1.setPen(AXIS_PEN)
                    ax = self.multiplot[i].getAxis("bottom")
                    ax.setPen(AXIS_PEN)
            for k, col in enumerate(self.data):
                self.multiplot[k].plot(np.array(self.data[self.timeCol][1:]).astype(np.float),
                                       np.array(col[1:]).astype(np.float),
                                       clear=True,
                                       title=self.plots[k].name,
                                       pen=self.plots[k].color,
                                       symbol=self.symbol,
                                       symbolPen=SYMBOL_PEN,
                                       symbolBrush=self.plots[k].color)
                self.multiplot[k].setTitle(self.plots[k].name, color=self.plots[k].color)
                self.setxaxis(self.multiplot[k], len(self.data))

            self.ran2 = False

    def setxaxis(self, widget, iterate=1):
        global SetAxis
        if SetAxis:
            widget.enableAutoRange(True, y=1)
            if self.runIterator != iterate:
                try:
                    self.minrange = int(ui.lineEditMin.text())
                    self.maxrange = int(ui.lineEditMax.text())
                except:
                    if (ui.lineEditMin.text() == ""):
                        self.minrange = 0
                        ui.lineEditMin.setText("0")
                    if (ui.lineEditMax.text() == ""):
                        self.maxrange = 0
                        ui.lineEditMax.setText("0")
                        # print("exception")
                self.displaypoints = ui.spinBoxPoints.value()
                if (self.minrange == 0 and self.maxrange == 0 and self.displaypoints == 0) or (
                                ui.lineEditMin.text() == "" or ui.lineEditMax.text() == ""):
                    ui.spinBoxPoints.setEnabled(True)
                    widget.enableAutoRange(enable=True)
                    # print(1)

                elif (self.minrange != 0 and self.maxrange != 0 and self.displaypoints != 0) or (
                            self.maxrange < self.minrange):
                    ui.warningdialog("This makes no sense! Use your brain.")
                    ui.spinBoxPoints.setValue(0)
                    ui.lineEditMax.clear()
                    ui.lineEditMin.clear()
                    ui.minrange = 0
                    ui.maxrange = 0
                    widget.enableAutoRange(enable=True)
                    # print(2)
                elif (self.minrange or self.maxrange):
                    ui.spinBoxPoints.setEnabled(False)
                    if ui.lineEditMin.text() == "" and ui.lineEditMax.text() == "":
                        ui.spinBoxPoints.setEnabled(True)
                    widget.setXRange(self.minrange, self.maxrange, padding=0)
                    # print(3)

                elif self.displaypoints:
                    widget.setXRange(int(self.data[self.timeCol][-self.displaypoints]),
                                     int(self.data[self.timeCol][-1]), padding=.001)
                    widget.enableAutoRange(True, y=1)
                    # print(4)
                self.runIterator += 1
            else:
                self.runIterator = 0
                SetAxis = False

    def iniserial(self):
        self.ui.actionPort.triggered.connect(partial(self.serialmenuconnect, 1))
        self.ui.actionStart_Comms.triggered.connect(partial(self.serialmenuconnect, 2))
        self.ui.actionPause_Comms.triggered.connect(partial(self.serialmenuconnect, 3))
        self.ui.actionEnd_Comms.triggered.connect(partial(self.serialmenuconnect, 4))

    def inicommand(self):
        self.ui.pushButtonCam.clicked.connect(partial(self.paramsend, CAM_CMD))
        self.ui.pushButtonRelease.clicked.connect(partial(self.paramsend, RELEASE_CMD))
        self.ui.toolButtonPauseTerm.clicked.connect(self.scrollterm)
        self.ui.pushButtonSetRange.clicked.connect(self.setaxisbool)
        self.ui.pushButtonSetPoints.clicked.connect(self.setaxisbool)
        self.ui.pushButtonImg.clicked.connect(self.loadimage)
        self.ui.pushButtonParam.clicked.connect(partial(self.paramsend, "p"))

    def inifilemmenu(self):
        self.ui.actionSave_Figure.triggered.connect(self.exportdialog)

    def serialcomms(self, port):
        try:
            print("Serial Thread start")
            serialObj = serial.Serial(port=port,
                                      baudrate=57600,
                                      parity=serial.PARITY_NONE,
                                      stopbits=serial.STOPBITS_ONE,
                                      bytesize=serial.EIGHTBITS,
                                      timeout=.05,
                                      rtscts=0,
                                      xonxoff=0,
                                      dsrdtr=0)
            serialObj.flushInput()
            serialObj.flushOutput()
            run = 0
            #global SerialThreadStart
            #SerialThreadStart = True
            while (True):
                # print("looping")
                try:
                    serState = serialStateQ.get()
                    if (serState):
                        print(serState)
                        # print(serState)
                except serialStateQ.empty:
                    # print(serState + 'emptyq')
                    pass
                if (serState == "End Serial"):
                    serialObj.close()
                    print("Serial Comms Ended Successfully")
                    serialSendQ.put('end')
                    while (serialStateQ.empty == False):
                        print('...')
                        serialStateQ.get()
                    print('Process End')
                    # global SerialThreadStart
                    # SerialThreadStart = False
                    return
                if (serialSendQ.empty() == False):
                    temp = serialSendQ.get(0)
                    for i in range(50):
                        serialObj.write(temp)
                        time.sleep(0.02)
                try:
                    if (serialObj.inWaiting() and serState == "Start Serial"):
                        serialData = serialObj.readline()
                        print(repr(serialData))
                        # serialObj.flushInput()
                        if (
                                            serialData == "sending picture\n" or serialData == "sending picture" or serialData == "sending picture\r\n"):
                            run += 1
                            print(run)
                            serialData = ""
                            length = serialObj.readline()
                            length = length.rstrip()
                            print(repr(length))
                            img = open(JPG_NAME, "w")
                            imgBytelist = []
                            timePrev = time.time()
                            while (True):
                                if (serialObj.inWaiting()):
                                    dat = serialObj.read()
                                    img.write(dat)
                                    imgBytelist.append(dat)
                                    print (len(imgBytelist), ' Bytes ')
                                    try:
                                        if (len(imgBytelist) > int(length) or (time.time() - timePrev) >= IMG_TIMEOUT):
                                            print("Image Recieved")
                                            serialObj.flushInput()
                                            serialObj.flushOutput()
                                            img.close()
                                            break
                                    except:
                                        img.close()
                                        print(sys.exc_info()[0])
                                        break
                        if (serialData.startswith(TEAM_ID)):
                            serialDataQ.put(serialData, 0)
                            serialObj.flushInput()
                except serial.SerialException:
                    print("Serial Failed")
                    return
        except serial.SerialException:
            print("Serial Failed")
            # global SerialThreadStart
            # SerialThreadStart = False
            return

    def serialmenuconnect(self, case):
        print(case)
        if case == 1:
            while (True):
                self.port, choice = self.ui.inputdialog("Port", "Input Port (/dev/tty or COM)")
                try:
                    test = serial.Serial(port=self.port)
                    test.close()
                    self.PortSet = True
                    print(self.PortSet)
                    break
                except:
                    if (not choice):
                        self.PortSet = False
                        return
                    else:
                        self.ui.warningdialog("Not a valid port, try again.")
                        self.PortSet = False
        elif case == 2 and self.PortSet:
            serialStateQ.put("Start Serial")
            processstart(self.serialcomms, (self.port,), False)
            print("starting serial...")
        elif case == 3 and self.PortSet:
            serialStateQ.put("Stop Serial")
        elif case == 4 and self.PortSet:
            serialStateQ.put("End Serial")
        else:
            self.ui.warningdialog("Need to enter valid port!")

    def paramsend(self, cmd):
        if (serialSendQ.empty()):
            if (cmd == "p"):
                cmd = str(ui.lineEditParam.text()) + '\n'
            print("Sending: " + cmd)
            serialSendQ.put(cmd)
        else:
            ui.warningdialog("Still sending previous packet!")

    def scrollterm(self):
        if (not self.scroll):
            self.ui.plainTextEditTerm.moveCursor(QtGui.QTextCursor.End)
            self.ui.plainTextEditTerm.setEnabled(False)
            # self.plainTextEditTerm.setStyleSheet("color:black; background-color:white")
        else:
            self.ui.plainTextEditTerm.setEnabled(True)
        self.scroll = not self.scroll

    def setaxisbool(self):
        global SetAxis
        SetAxis = True

    def loadimage(self):
        if (self.imgPathSet == False):
            self.imgPath = QtGui.QFileDialog.getOpenFileName(self.ui, 'Open file', '/home')
        else:
            pass
        f = Image.open(str(self.imgPath))
        f.save("tempimg.png")
        pixmap = QtGui.QPixmap("tempimg.png")
        # arr = np.array(f.getdata())
        self.ui.imgView.setPixmap(pixmap)

    def exportdialog(self):
        self.exporter = pg.exporters.ImageExporter(self.ui.graphicsView.scene())
        self.exporter.fileSaveDialog()


class Graphics():  # can add functionality for inputting data to display
    def __init__(self, ui, backend):
        self.setup3D(ui)
        self.timer2 = pg.QtCore.QTimer()
        self.timer2.timeout.connect(self.update3D)
        self.timer2.start(1000)
        self.backend = backend

    def setup3D(self, ui):
        ui.GLWidget.setCameraPosition(distance=2.75, azimuth=180, elevation=60)
        ui.GLWidget.pan(-0.25,0,0)
        self.grid1 = gl.GLGridItem()
        self.ax1 = gl.GLAxisItem()
        self.ax2 = gl.GLAxisItem()
        self.ax3 = gl.GLAxisItem()

        ui.GLWidget.addItem(self.grid1)
        ui.GLWidget.addItem(self.ax1)
        ui.GLWidget.addItem(self.ax2)
        ui.GLWidget.addItem(self.ax3)

        self.ax1.setSize(5, 5, 5)
        self.ax2.setSize(5, 5, 5)
        self.ax3.setSize(5, 5, 5)

        self.ax2.rotate(180, 0, 1, 0)
        self.ax3.rotate(180, 0, 0, 1)

        self.grid1.translate(0, 0, -0.1)
        ##------------------------------------------------------------
        ## ARROW
        self.parseObj = OBJparser("arrow.obj")
        self.verts = np.asarray(self.parseObj.vertices)
        self.faces = []
        for i in range(len(self.parseObj.faces)):
            self.faces.append(self.parseObj.faces[i][0])
        self.faces = np.asarray(self.faces)
        self.verts = np.asarray(self.parseObj.vertices)

        self.arrow = gl.GLMeshItem(vertexes=self.verts, faces=self.faces, smooth=False)
        self.arrow.setGLOptions('opaque')
        self.arrow.setShader('viewNormalColor')
        ui.GLWidget.addItem(self.arrow)
        ##------------------------------------------------------------
        ## TICKS NSEW
        self.parseObj = OBJparser("ticks.obj")
        self.verts = np.asarray(self.parseObj.vertices)
        self.faces = []
        for i in range(len(self.parseObj.faces)):
            self.faces.append(self.parseObj.faces[i][0])
        self.faces = np.asarray(self.faces)
        self.verts = np.asarray(self.parseObj.vertices)

        self.ticks = gl.GLMeshItem(vertexes=self.verts, faces=self.faces, smooth=False)
        self.ticks.setGLOptions('opaque')
        self.ticks.setShader('viewNormalColor')
        ui.GLWidget.addItem(self.ticks)
        self.ticks.rotate(90,1,0,0)




        self.height = 0
        self.xangle = 0
        self.yangle = 0
        self.zangle = 0
        self.heightprev = 0
        self.xangleprev = 0
        self.yangleprev = 0
        self.zangleprev = 0

    def update3D(self):

        self.zangle = int(self.backend.data[1][-1])

        self.ax1.translate(0, 0, -self.heightprev)
        self.ax2.translate(0, 0, -self.heightprev)
        self.ax3.translate(0, 0, -self.heightprev)
        self.arrow.translate(0, 0, -self.heightprev)
        self.arrow.rotate(-self.xangleprev, 1, 0, 0)
        self.arrow.rotate(-self.yangleprev, 0, 1, 0)
        self.arrow.rotate(-self.zangleprev, 0, 0, 1)

        self.ax1.translate(0, 0, self.height)
        self.ax2.translate(0, 0, self.height)
        self.ax3.translate(0, 0, self.height)
        self.arrow.translate(0, 0, self.height)
        self.arrow.rotate(self.xangle, 1, 0, 0)
        self.arrow.rotate(self.yangle, 0, 1, 0)
        self.arrow.rotate(self.zangle, 0, 0, 1)

        if self.heightprev != self.height:
            self.heightprev = self.height
        if self.xangleprev != self.xangle:
            self.xangleprev = self.xangle
        if self.yangleprev != self.yangle:
            self.yangleprev = self.yangle
        if self.zangleprev != self.zangle:
            self.zangleprev = self.zangle  # can add functionality fo


class OBJparser:
    def __init__(self, filename, swapyz=False):
        """ Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]) - 1)
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append([face, norms, texcoords, material])


class TermRedirect():
    def __init__(self, widget, oldobj):
        self.widget = widget
        self.oldobj = oldobj
        self.index = 1
        pass

    def write(self, Str):
        self.widget.setReadOnly(False)
        # self.widget.setEnabled(False)
        # self.widget.moveCursor(QtGui.QTextCursor.End)
        if self.scroll:
            self.widget.moveCursor(QtGui.QTextCursor.End)
        if Str != '\n':
            self.widget.insertPlainText(str(self.index) + ": ")
            self.index += 1
        # self.oldobj.write(repr(Str))
        self.widget.insertPlainText(Str)
        self.widget.setReadOnly(True)
        self.oldobj.write(Str)

        pass

    def flush(self):
        pass


class plotObjs:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.unit = ""

class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return []


from pyqtgraph import PlotWidget

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    ui = Ui_MainWindow()
    ui.begin()
    B = Backend(ui)
    G = Graphics(ui, B)
    oldstdout = sys.stdout
    sys.stdout = TermRedirect(ui.plainTextEditTerm, oldstdout)

    sys.exit(app.exec_())
