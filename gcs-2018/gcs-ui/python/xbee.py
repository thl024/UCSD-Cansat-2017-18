# XBee Stuffs
def update():
	pass

class XBeeCommunicator():

	def __init__(self):
		pass

	def connect():
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

	def start():
		serialStateQ.put("Start Serial")
        processstart(self.serialcomms, (self.port,), False)
        print("starting serial...")

    def pause():
    	serialStateQ.put("Stop Serial")

    def end():
    	serialStateQ.put("End Serial")


# Connect
def serialmenuconnect(self, case):
        print(case)
        if case == 1:
            
        elif case == 2 and self.PortSet:
            
        elif case == 3 and self.PortSet:
            
        elif case == 4 and self.PortSet:
            
        else:
            self.ui.warningdialog("Need to enter valid port!")

