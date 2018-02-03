class XBeeCommunicator():

    def __init__(self):
        self.connected = False
        pass

    def connect(self, port):
        try:
            # test = serial.Serial(port=self.port)
            # test.close()
            self.connected = True
            print("Connected to XBee.")
            return True
        except:
            return False

    def start(self):
        if not self.connected:
           return False

        ## serialStateQ.put("Start Serial")
        # processstart(self.serialcomms, (self.port,), False)
        print("Starting XBee Connection")
        return True

    def pause(self):
        if not self.connected:
           return False

        # serialStateQ.put("Pausing XBee Connection")
        print("Pausing XBee Connection")
        return True

    def stop(self):
        if not self.connected:
            return False

        # serialStateQ.put("Stopping XBeeConnection")
        print("Stopping XBee Connection")
        return True

