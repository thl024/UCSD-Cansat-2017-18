import serial
import time
from random import randint

from PyQt5.QtCore import pyqtSignal, QThread

class XBeeCommunicator():

    def __init__(self):
        self.connected = False
        self.ser = None
        self.xbee_thread = None
        pass

    def connect(self, port):
        try:
            self.connected = True

            # Open connection
            # self.ser = serial.Serial(port)

            print("Connected to XBee.")
            return True
        except:
            return False

    def start(self, callback):
        if not self.connected:
           return False
        
        self.begin_thread(callback)

        print("Starting XBee Connection")
        return True

    def pause(self):
        if not self.connected:
           return False

        self.stop_thread()

        print("Pausing XBee Connection")
        return True

    def stop(self):
        self.connected = False
        self.stop_thread()

        # Close connection
        # if self.ser:
        #     self.ser.close()
        #     self.ser = None

        print("Stopping XBee Connection")
        return True

    def snapshot(self):
        if not self.connected:
            return False

        # Send signal

        print("Snapshot Taken")
        return True

    def begin_thread(self, callback):
        self.xbee_thread = XBeeThread()
        self.xbee_thread.update.connect(callback)
        self.xbee_thread.start()

    def stop_thread(self):
        self.xbee_thread.stop = True


class XBeeThread(QThread):
    update = pyqtSignal(list)
    stop = False

    def run(self):
        while not self.stop:
            # with serial.Serial('/dev/ttyS1', 19200, timeout=1) as ser:
            #     x = ser.read()          # read one byte
            #     s = ser.read(10)        # read up to ten bytes (timeout)
            #     line = ser.readline()   # read a '\n' terminated line

            randdata = [randint(0, 300) for n in range(0, 16)]
            self.update.emit(randdata)
            time.sleep(3)

        pass
