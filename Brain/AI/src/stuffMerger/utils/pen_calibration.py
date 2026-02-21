import queue
from time import sleep
import pickle

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression, HuberRegressor, RANSACRegressor
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
import os

from sklearn.multioutput import MultiOutputRegressor

from AI.src.stuffMerger.utils.gesture_tracker import GestureTracker
from AI.src.constants import logger, CLIENT_PATH, TAPPY_ORIGINAL_SERVER_IP


class SwipeCalibrator:
	"""
	Parameters:
		method: "linear_regression" (default), "linear_interpolation", "ransac_regression", "huber_regression"
	"""
	def __init__(self, method: str = "linear_regression"):
		self.is_trained = False
		self.cmds = []
		self.acts = []

		self.method = method
		self.model = None
		self.fallback_model = None

	
	def train(self,
	          commanded_swipes: list[list[int]] | None = None,
	          measured_swipes: list[list[int]] | None = None,
	          method: str | None = None,
	          drop_first: bool = False,
	          outlier_zscore_thresh: float | None = None,
		):
		"""
		Parameters:
			commanded_swipes: A list of pairs (dx, dy) that the pen should have performed
			measured_swipes: A list of pairs (dx, dy) that the pen actually performed
			method: None (default, will use the one used in the class creation),
				"linear_regression", "linear_interpolation", "ransac_regression", "huber_regression"
			drop_first: if True, drop the first sample (useful if the first capture is noisy)
			outlier_zscore_thresh: if not None, remove measured samples with z-score > thresh (on measured magnitude)
		"""
		if commanded_swipes is None:
			commanded_swipes = self.cmds
		if measured_swipes is None:
			measured_swipes = self.acts
		
		if len(commanded_swipes) == 0 or len(measured_swipes) == 0:
			raise ValueError("No training data provided")
		
		measured = np.array(measured_swipes)
		commanded = np.array(commanded_swipes)
		
		if measured.shape[0] != commanded.shape[0]:
			raise ValueError("Measured and commanded lists must have same length")
		
		if drop_first:
			if measured.shape[0] <= 1:
				raise ValueError("Not enough points to drop first sample")
			measured = measured[1:]
			commanded = commanded[1:]
		
		if outlier_zscore_thresh is not None and measured.shape[0] >= 3:
			mags = np.linalg.norm(measured, axis=1)
			m_mean = np.mean(mags)
			m_std = np.std(mags)
			if m_std > 0:
				z = (mags - m_mean) / m_std
				mask = np.abs(z) <= outlier_zscore_thresh
				if not np.all(mask):
					logger.info(f"Removing {np.sum(~mask)} outlier(s) from calibration data by z-score")
					measured = measured[mask]
					commanded = commanded[mask]
		
		if method is None:
			method = self.method
		
		if method == 'linear_regression':
			self.model = LinearRegression()
			self.model.fit(measured, commanded)
		elif method == 'huber_regression':
			self.model = MultiOutputRegressor(HuberRegressor())
			self.model.fit(measured, commanded)
		elif method == 'ransac_regression':
			self.model = RANSACRegressor(LinearRegression(), random_state=0)
			self.model.fit(measured, commanded)
		elif method == 'linear_interpolation':
			self.model = LinearNDInterpolator(measured, commanded)
			self.fallback_model = NearestNDInterpolator(measured, commanded)
		else:
			raise ValueError(f"Unknown calibration method: {method}")
		
		self.is_trained = True
		logger.info(f"Calibration complete using {self.method}.")
	
	def _predict(self, inputs):
		if self.method == 'linear_interpolation':
			res = self.model(inputs)
			if np.any(np.isnan(res)):
				nans = np.isnan(res).any(axis=1)
				res[nans] = self.fallback_model(inputs[nans])
			return res
		return self.model.predict(inputs)
		
	def get_calibrated_command(self, target_dx, target_dy) -> tuple[float, float]:
		"""
		Returns:
			the [x, y] command needed to achieve the target swipe
		"""
		if not self.is_trained:
			return target_dx, target_dy
		
		prediction = self._predict(np.array([[target_dx, target_dy]]))
		return prediction[0]
	
	def plot_vector_calibration(self, max_range: int = 1000, save_path: str = "calibration_map.png"):
		"""
		Generates the visualization of the calibration map with vectors
		
		Parameters:
			max_range: the max offset
			save_path: path to save the plot
		"""
		if not self.is_trained:
			raise ValueError("Train the model first!")
		
		grid_size = 10
		x, y = np.meshgrid(np.linspace(0, max_range, grid_size), np.linspace(0, max_range, grid_size))
		
		flat_x, flat_y = x.flatten(), y.flatten()
		targets = np.column_stack((flat_x, flat_y))
		commands = self._predict(targets)
		
		plt.figure(figsize=(8, 6))
		# Plot the 'push' vectors: (Command - Target)
		plt.quiver(flat_x, flat_y, commands[:, 0] - flat_x, commands[:, 1] - flat_y, color='blue', alpha=0.6,
		           label='Correction Vector')

		plt.title(f"Calibration Map: Required 'Push' to overcome Friction ({self.method})")
		plt.xlabel("Desired X Displacement")
		plt.ylabel("Desired Y Displacement")
		plt.legend()
		plt.grid(True)
		if save_path:
			plt.savefig(save_path)
			logger.info(f"Plot saved to {save_path}")
		plt.show()

	def plot_heatmap_calibration(self, max_range: int = 1000, save_path: str = "calibration_heatmap.png"):
		"""
		Generates a heatmap visualization of the calibration map showing the magnitude of correction.
		
		Parameters:
			max_range: the max offset
			save_path: path to save the plot
		"""
		if not self.is_trained:
			raise ValueError("Train the model first!")
		
		grid_size = 50
		x_linspace = np.linspace(0, max_range, grid_size)
		y_linspace = np.linspace(0, max_range, grid_size)
		X, Y = np.meshgrid(x_linspace, y_linspace)
		
		flat_x, flat_y = X.flatten(), Y.flatten()
		targets = np.column_stack((flat_x, flat_y))
		commands = self._predict(targets)
		
		# Calculate the magnitude of the correction vector (Command - Target)
		correction_vectors = commands - targets
		correction_magnitudes = np.linalg.norm(correction_vectors, axis=1)
		Z = correction_magnitudes.reshape(X.shape)
		
		plt.figure(figsize=(10, 8))
		plt.pcolormesh(X, Y, Z, shading='auto', cmap='viridis')
		plt.colorbar(label='Correction Magnitude (pixels)')
		
		# Plot original training points if available (measured acts)
		if len(self.acts) > 0:
			acts_arr = np.array(self.acts)
			plt.plot(acts_arr[:, 0], acts_arr[:, 1], "ok", markersize=4, label="Measured Points")
			plt.legend(loc="upper right")
			
		plt.title(f"Calibration Heatmap: Correction Magnitude ({self.method})")
		plt.xlabel("Desired X Displacement")
		plt.ylabel("Desired Y Displacement")
		plt.axis("equal")
		
		if save_path:
			plt.savefig(save_path)
			logger.info(f"Heatmap saved to {save_path}")
		plt.show()

	def plot_connected_pairs(self, save_path: str = "calibration_pairs.png"):
		"""
		Plots the commanded vs measured swipes connected by lines.
		This helps visualize the error for each specific training point.
		
		Parameters:
			save_path: path to save the plot
		"""
		if len(self.cmds) == 0 or len(self.acts) == 0:
			raise ValueError("No training data available to plot pairs")
		
		cmds_arr = np.array(self.cmds)
		acts_arr = np.array(self.acts)
		
		if len(cmds_arr) != len(acts_arr):
			logger.warning("Commands and Acts arrays have different lengths, truncating to minimum")
			min_len = min(len(cmds_arr), len(acts_arr))
			cmds_arr = cmds_arr[:min_len]
			acts_arr = acts_arr[:min_len]
			
		plt.figure(figsize=(10, 8))
		
		# Plot commanded points
		plt.scatter(cmds_arr[:, 0], cmds_arr[:, 1], c='blue', label='Commanded (Desired)', marker='o')
		
		# Plot measured points
		plt.scatter(acts_arr[:, 0], acts_arr[:, 1], c='red', label='Measured (Actual)', marker='x')
		
		# Draw lines connecting them
		for i in range(len(cmds_arr)):
			plt.plot([cmds_arr[i, 0], acts_arr[i, 0]], [cmds_arr[i, 1], acts_arr[i, 1]], 'k-', alpha=0.3)
			
		plt.title("Calibration: Commanded vs Measured Pairs")
		plt.xlabel("X Displacement")
		plt.ylabel("Y Displacement")
		plt.legend()
		plt.grid(True)
		plt.axis("equal")
		
		if save_path:
			plt.savefig(save_path)
			logger.info(f"Pairs plot saved to {save_path}")
		plt.show()
	
	def automatic_calibration(self):
		gesture_queue = queue.Queue()
		tracker = GestureTracker(gesture_queue)
		tracker.start()
		
		# Get X data
		for i in range(2, 9):
			self.cmds.append([100 * i, 0])
			os.system(f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {200 + 100 * i} {1000}'")
			sleep(3)
			
		# Get X half step
		for i in range(1, 9, 2):
			self.cmds.append([200 + 50 * i, 0])
			os.system(f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {200 + 200 + 50 * i} {1000}'")
			sleep(3)
		
		# Get Y data
		for i in range(2, 9):
			self.cmds.append([0, 100 * i])
			os.system(f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {500} {200} {500} {200 + 100 * i}'")
			sleep(3)
			
		# Get Y half step
		for i in range(1, 9, 2):
			self.cmds.append([0, 200 + 50 * i])
			os.system(f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {500} {200} {500} {200 + 200 + 50 * i}'")
			sleep(3)
			
		# Get XY Data combined
		for i in range(2, 9):
			self.cmds.append([100 * i, 100 * i])
			os.system(
				f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {200} {200 + 100 * i} {200 + 100 * i}'")
			sleep(3)
			
		# Get XY Data combined half step
		for i in range(1, 9, 2):
			self.cmds.append([200 + 50 * i, 200 + 50 * i])
			os.system(
				f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {200} {200 + 200 + 50 * i} {200 + 200 + 50 * i}'")
			sleep(3)
	
		# Dummy capture Because my capturer capture the next group based on adb timestamp
		os.system(f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {500} {1000}'")
		sleep(3)
		
		queue_to_list = [gesture_queue.get(timeout=5) for _ in range(gesture_queue.qsize())]
		for cmd, gesture in zip(self.cmds, queue_to_list):
			logger.info(gesture)
			logger.info(f"[🧪] ({cmd})")
			self.acts.append([gesture.end_x - gesture.start_x, gesture.end_y - gesture.start_y])
		
		tracker.stop()
		tracker.join()
	
	def automatic_deep_calibration(self):
		"""
		Calibrate by setting an objective (600,0) and perform multiple actions until you get close to (600,0)
		Collects a lot of data and it's slow
		"""
		pass
	
	def manual_calibration(self):
		pass
	
	def manual_expand_calibration(self):
		"""
		Add calibration point to the existing ones [⚠️WARNING will damage the automatic_deep_calibration]
		The naming "manual_" assumes exists "autmatic_" calibration but researchers were not able to find it
		"""
		pass
	
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
	
	cal = SwipeCalibrator(method='linear_regression')
	
	if True:
		cal.load("test_0_example_calibration.pkl")
	else:
		cal.automatic_calibration()
		cal.save("test_0_example_calibration.pkl")
	
	cal.train(method='linear_regression')
	cal.plot_vector_calibration()
	cal.plot_heatmap_calibration()
	cal.plot_connected_pairs()
	
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