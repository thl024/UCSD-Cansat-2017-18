import serial
import time
from threading import Thread
from random import randint

class XBeeCommunicator():

    def __init__(self):
        self.connected = False
        self.ser = None
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

    def start(self, threaded_function):
        if not self.connected:
           return False

        # Begin reading - create a threaded process
        self.keep_threading = True
        thread = Thread(target = self.receive_data_threaded, args = [threaded_function])
        thread.start()

        print("Starting XBee Connection")
        return True

    def pause(self):
        if not self.connected:
           return False

        # Stop reading
        self.keep_threading = False

        print("Pausing XBee Connection")
        return True

    def stop(self):
        self.connected = False
        self.keep_threading = False

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

    def receive_data_threaded(self, threaded_function):

        while (self.keep_threading):

            # with serial.Serial('/dev/ttyS1', 19200, timeout=1) as ser:
            #     x = ser.read()          # read one byte
            #     s = ser.read(10)        # read up to ten bytes (timeout)
            #     line = ser.readline()   # read a '\n' terminated line

            randdata = [randint(0, 300) for n in range(0, 16)]
            threaded_function(randdata)
            time.sleep(3)

            pass
