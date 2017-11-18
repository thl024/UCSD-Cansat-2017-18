import pandas as pd

class DataLoader():

	def __init__(self, file_name):
		self.file_name = file_name
		self.data = []

	def read_file(self):
		mat = []
		with open(self.file_name) as f:
			for line in f.read().split("\n") :
				mat.append(line.strip("\n").split(","))
		self.data = pd.DataFrame(mat[2:len(mat) - 1], columns=mat[0])

	def fetch(self, columns):
		print(self.data[columns])