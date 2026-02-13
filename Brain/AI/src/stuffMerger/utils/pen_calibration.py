import queue
from time import sleep
import pickle

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import os

from AI.src.stuffMerger.utils.gesture_tracker import GestureTracker
from AI.src.constants import logger, CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP


class SwipeCalibrator:
	def __init__(self, ):
		self.model = LinearRegression()
		self.is_trained = False
		self.cmds = []
		self.acts = []
	
	def train(self, commanded_swipes: list[list[int]] | None = None, measured_swipes: list[list[int]] | None = None):
		"""
		Expects lists/arrays of [dx, dy]
		commanded_swipes: What you sent to the motors
		measured_swipes: What the pen actually did
		"""
		if commanded_swipes is None:
			commanded_swipes = self.cmds
		if measured_swipes is None:
			measured_swipes = self.acts
		
		x = np.array(measured_swipes)
		y = np.array(commanded_swipes)
		self.model.fit(x, y)
		self.is_trained = True
		logger.info("Calibration complete.")
	
	def get_calibrated_command(self, target_dx, target_dy):
		"""Returns the [x, y] command needed to achieve the target swipe"""
		if not self.is_trained:
			raise ValueError("Model is not trained!")
		
		prediction = self.model.predict([[target_dx, target_dy]])
		return prediction[0]
	
	def plot_calibration(self, max_range=1000, save_path="calibration_map.png"):
		"""Generates the visualization of the calibration map"""
		if not self.is_trained:
			print("Train the model first!")
			return
		
		grid_size = 10
		x, y = np.meshgrid(np.linspace(0, max_range, grid_size), np.linspace(0, max_range, grid_size))
		
		flat_x, flat_y = x.flatten(), y.flatten()
		targets = np.column_stack((flat_x, flat_y))
		commands = self.model.predict(targets)
		
		plt.figure(figsize=(8, 6))
		# Plot the 'push' vectors: (Command - Target)
		plt.quiver(flat_x, flat_y, commands[:, 0] - flat_x, commands[:, 1] - flat_y, color='blue', alpha=0.6,
		           label='Correction Vector')

		plt.title("Calibration Map: Required 'Push' to overcome Friction")
		plt.xlabel("Desired X Displacement")
		plt.ylabel("Desired Y Displacement")
		plt.legend()
		plt.grid(True)
		if save_path:
			plt.savefig(save_path)
			print(f"Plot saved to {save_path}")
		plt.show()
	
	def calibrate(self):
		gesture_queue = queue.Queue()
		tracker = GestureTracker(gesture_queue)
		tracker.start()
		
		# Get x data
		for i in range(2, 9):
			self.cmds.append([100 * i, 0])
			os.system(f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {200 + 100 * i} {1000}'")
			sleep(3)
		
		# Get Y data
		for i in range(2, 9):
			self.cmds.append([0, 100 * i])
			os.system(f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {500} {200} {500} {200 + 100 * i}'")
			sleep(3)
		
		# Dummy capture Because my capturer capture the next group based on adb timestamp
		os.system(f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {500} {1000}'")
		sleep(3)
		
		# Process X Data
		for i in range(2, 9):
			gesture = gesture_queue.get(timeout=5)
			logger.info(gesture)
			logger.info(f"[🧪] ({self.cmds[i - 2]})")
			self.acts.append([gesture.end_x - gesture.start_x, gesture.end_y - gesture.start_y])
		
		# Process Y Data
		for i in range(2, 9):
			gesture = gesture_queue.get(timeout=5)
			logger.info(gesture)
			logger.info(f"[🧪] ({self.cmds[i + 5]})")  # 7-2=5
			self.acts.append([gesture.end_x - gesture.start_x, gesture.end_y - gesture.start_y])
			
		tracker.stop()
		tracker.join()
	
	def load(self, filename: str | None = "dati_xy.pkl"):
		if not filename.endswith(".pkl"):
			raise ValueError("File must be a pickle file")
		
		with open(filename, 'rb') as f:
			caricato = pickle.load(f)
		
		self.cmds = caricato["cmds"]
		self.acts = caricato["acts"]
	
	def save(self, filename: str | None = "dati_xy.pkl"):
		if not filename.endswith(".pkl"):
			raise ValueError("File must be a pickle file")
		
		data_to_save = {"cmds": self.cmds, "acts": self.acts}
		
		with open(filename, 'wb') as f:
			pickle.dump(data_to_save, f)


if __name__ == "__main__":
	TAPPY_ORIGINAL_SERVER_IP = "http://127.0.0.1:8000"
	CLIENT_PATH = "/home/wip/tesi/BrainyBot/tappy-client/clients/python"
	
	cal = SwipeCalibrator()
	
	if True:
		cal.load()
	else:
		cal.calibrate()
		cal.save()
	
	cal.train()
	cal.plot_calibration()
	
	gesture_queue = queue.Queue()
	tracker = GestureTracker(gesture_queue)
	tracker.start()
	
	try:
		taget_x = int(input("x:"))
		taget_y = int(input("y:"))
		
		cmd_needed = cal.get_calibrated_command(taget_x, taget_y)
		
		# Test swipe
		os.system(
			f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {100} {1000} {100 + int(cmd_needed[0])} {1000 + int(cmd_needed[1])}'")
		sleep(3)
		# Dummy
		os.system(
			f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {500} {1000}'")
		sleep(3)
		
		logger.info(
			f"\n{gesture_queue.get(timeout=5)}\n[🧪]: {taget_x}, {taget_y}\n[🚂]: X={cmd_needed[0]:.2f}, Y={cmd_needed[1]:.2f}")
		
		while True:
			taget_x = int(input("x:"))
			taget_y = int(input("y:"))
			
			cmd_needed = cal.get_calibrated_command(taget_x, taget_y)
			
			
			# Test swipe
			os.system(
				f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {100} {1000} {100 + int(cmd_needed[0])} {1000 + int(cmd_needed[1])}'")
			sleep(3)
			# Burn previous dummy
			gesture_queue.get()
			# Dummy
			os.system(
				f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {500} {1000}'")
			sleep(3)
			
			logger.info(f"\n{gesture_queue.get(timeout=5)}\n[🧪]: {taget_x}, {taget_y}\n[🚂]: X={cmd_needed[0]:.2f}, Y={cmd_needed[1]:.2f}")

	finally:
		logger.info("Exiting...")
		tracker.stop()
		tracker.join()