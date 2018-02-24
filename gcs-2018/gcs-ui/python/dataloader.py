import pandas as pd

HEADERS = ["TeamID", "Time", "Packet", "Altitude", "Pressure", "Airspeed", "Temperature", "Voltage", "Latitude", "Longitude",
"GPSAlt", "Satellites", "GPSSpeed", "Heading", "ImageCount", "State"]

# loads in data from the passed in filename
class DataLoader():

    # define variables to store data
    def __init__(self, file_name):
        self.file_name = file_name
        self.data = pd.DataFrame(columns=HEADERS)

    # read lines from the file passed in
    def read_file(self):
        mat = []
        with open(self.file_name) as f:
            for line in f.read().split("\n") :
                mat.append(line.strip("\n").split(","))

        # neatly format data using pandas
        self.data = pd.DataFrame(mat[1:len(mat) - 1], columns=mat[0])

    # Assume all parameters recording
    def update(self, columns, new_data):
        if not len(columns) == len(new_data):
            return False
        self.data.loc[len(self.data)] = new_data
        timeCount = self.data.iloc[len(self.data) - 2]["Time"]
        self.data.iloc[len(self.data) - 1]["Time"] = int(timeCount) + 1
        self.save_as_csv()

    # access data by passing in column names
    def fetch(self, columns):
        if (columns == "All"):
            return self.data
        else:
            return self.data[columns]

    # Save current dataframe to CSV file
    def save_as_csv(self):
        self.data.to_csv(self.file_name, columns=HEADERS, index=False)
