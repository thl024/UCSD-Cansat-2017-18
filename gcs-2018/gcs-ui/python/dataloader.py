import pandas as pd

# loads in data from the passed in filename
class DataLoader():

    # define variables to store data
    def __init__(self, file_name):
        self.file_name = file_name
        self.data = []

    # read lines from the file passed in
    def read_file(self):
        mat = []
        with open(self.file_name) as f:
            for line in f.read().split("\n") :
                mat.append(line.strip("\n").split(","))
        # neatly format data using pandas
        self.data = pd.DataFrame(mat[2:len(mat) - 1], columns=mat[0])

    # Assume all parameters recording
    def update(self, columns, new_data):
        if not len(columns) == len(new_data):
            return False
        self.data.loc[len(self.data)] = new_data

    # access data by passing in column names
    def fetch(self, columns):
        if (columns == "All"):
            return self.data
        else:
            return self.data[columns]       
