import queue
import re
import threading
import time
import math
import subprocess
import select
import os
import pty

from dataclasses import dataclass
from typing import Any

from AI.src.constants import logger

@dataclass  # Java to Kotlin: Watch what they need to imitate a FRACTION of our power
class Gesture:
	start_x: int
	start_y: int
	end_x: int
	end_y: int
	timestamp: float
	
	def __str__(self):
		dx = self.end_x - self.start_x
		dy = self.end_y - self.start_y
		dist = math.hypot(dx, dy)
		return (f"[⌚ ] {time.ctime(self.timestamp)}\n"
		        f"[🏁] ({self.start_x}, {self.start_y})\n"
		        f"[🏅] ({self.end_x}, {self.end_y})\n"
		        f"[📐] ({dx}, {dy}, {dist:.2f})")

class GestureTracker(threading.Thread):
	def __init__(self, output_queue: queue.Queue | None = queue.Queue()):
		super().__init__(daemon=True)
		self.output_queue = output_queue
		# You could add other stuff like finger touchdown and so on... it's out of my scope tough
		# use character class instead of single-char alternation to avoid a linter warning
		self.__pattern = re.compile(r"ABS_MT_POSITION_[XY]\s+([0-9a-f]+)")
		# timestamp at the start of the getevent -lt line, e.g. "[   1234.567890]"
		self.__ts_pattern = re.compile(r"^\[\s*([0-9]+\.[0-9]+)]")
		self.__stop = False
		self.__process = None
		# how long (seconds) without events counts as gesture separation
		self.inactivity_threshold = 1.0
	
	def run(self):
		master_fd, slave_fd = pty.openpty()
		
		try:
			self.__process = subprocess.Popen(
				['adb', 'shell', 'getevent', '-lt'],
				stdout=slave_fd,
				stderr=subprocess.PIPE,
				stdin=subprocess.PIPE,
				close_fds=True
			)
			os.close(slave_fd)
			
			curr_start: dict[str, Any] = {'X': None, 'Y': None}
			curr_end: dict[str, Any] = {'X': None, 'Y': None}
			active = False
			last_event_ts: float | None = None
			buffer = ""
			
			while not self.__stop:
				if self.__process.poll() is not None:
					break

				# 0.1 is just to be ready when the stop() command arrives
				# probably some better implementation using threading would be best but this is a side component
				rlist, _, _ = select.select([master_fd], [], [], 0.1)
				
				if not rlist:
					continue
				
				try:
					data = os.read(master_fd, 1024).decode('utf-8', errors='ignore')
				except OSError:
					break
				
				if not data:
					break
				
				buffer += data
				while '\n' in buffer:
					line, buffer = buffer.split('\n', 1)
					line = line.strip()
					if not line:
						continue
					
					ts_match = self.__ts_pattern.search(line)
					ts = float(ts_match.group(1)) if ts_match else None
					
					match = self.__pattern.search(line)
					if match:
						hex_val = match.group(1)
						if 'ABS_MT_POSITION_X' in line:
							axis = 'X'
						else:
							axis = 'Y'
						val = int(hex_val, 16)
						
						if active and (ts is not None) and (last_event_ts is not None):
							dt = ts - last_event_ts
							if dt > self.inactivity_threshold:
								s_x, s_y = curr_start['X'], curr_start['Y']
								e_x, e_y = curr_end['X'], curr_end['Y']
								if all(v is not None for v in [s_x, s_y, e_x, e_y]):
									ts_for_g = float(last_event_ts) if last_event_ts is not None else time.time()
									g = Gesture(int(s_x), int(s_y), int(e_x), int(e_y), ts_for_g)
									self.output_queue.put(g)
								
								curr_start = {'X': None, 'Y': None}
								curr_end = {'X': None, 'Y': None}
								active = False
						
						if not active:
							active = True
							curr_start = {'X': None, 'Y': None}
						
						if curr_start[axis] is None:
							curr_start[axis] = val
						curr_end[axis] = val
						
						if ts is not None:
							last_event_ts = ts
			
			if active:
				s_x, s_y = curr_start['X'], curr_start['Y']
				e_x, e_y = curr_end['X'], curr_end['Y']
				if all(v is not None for v in [s_x, s_y, e_x, e_y]):
					ts_for_g = float(last_event_ts) if last_event_ts is not None else time.time()
					g = Gesture(int(s_x), int(s_y), int(e_x), int(e_y), ts_for_g)
					self.output_queue.put(g)

		finally:
			try:
				os.close(master_fd)
			except Exception as e:
				logger.error(e)
				pass
			
			if self.__process:
				try:
					self.__process.terminate()
				except Exception as e:
					logger.error(e)
					pass

	def stop(self):
		self.__stop = True
		if self.__process:
			try:
				self.__process.terminate()
			except Exception as e:
				logger.error(e)
				pass


if __name__ == "__main__":
	gesture_queue = queue.Queue()
	
	tracker = GestureTracker(gesture_queue)
	tracker.start()
	
	logger.info("🔫... Non c'è l'emoji del fischietto")
	
	try:
		while True:
			try:
				gesture = gesture_queue.get(timeout=0.1)
				logger.info(f"\n{gesture}")
			except queue.Empty:
				continue

	except KeyboardInterrupt:
		logger.info("\nExiting...")
		tracker.stop()
		tracker.join()
