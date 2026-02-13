import asyncio
import queue
import re
import threading
import time
from dataclasses import dataclass
from typing import Any

from numpy.ma.core import sqrt

from AI.src.constants import logger

@dataclass  # Java to Kotlin: Watch what they need to imitate a FRACTION of our power
class Gesture:
	start_x: int
	start_y: int
	end_x: int
	end_y: int
	timestamp: float
	
	def __str__(self):
		return f"""[⌚ ] {time.ctime(gesture.timestamp)}
		[🏁] ({gesture.start_x}, {gesture.start_y})
		[🏅] ({gesture.end_x}, {gesture.end_y})
		[📐] ({gesture.end_x - gesture.start_x}, {gesture.end_y - gesture.start_y}, {sqrt((gesture.end_x - gesture.start_x) ** 2 + (gesture.end_y - gesture.start_y) ** 2)})"""


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
	
	async def _producer(self):
		self.__process = await asyncio.create_subprocess_exec('adb', 'shell', 'getevent', '-lt',
		                                                      stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
		process = self.__process
		
		# start with simple None defaults (avoid using type expressions as values)
		curr_start: dict[str, Any] = {'X': None, 'Y': None}
		curr_end: dict[str, Any] = {'X': None, 'Y': None}
		active = False
		last_event_ts: float | None = None
		
		while not self.__stop:
			try:
				line_bytes = await process.stdout.readline()
			except ValueError:
				break

			if not line_bytes:
				break
			line = line_bytes.decode(errors='ignore')
			
			# extract adb-provided timestamp if present
			ts_match = self.__ts_pattern.search(line)
			ts = float(ts_match.group(1)) if ts_match else None
			
			# check for axis events
			# pattern now captures the hex value in group 1
			match = self.__pattern.search(line)
			if match:
				hex_val = match.group(1)
				# determine axis from the line explicitly (safer than relying on a capture group)
				if 'ABS_MT_POSITION_X' in line:
					axis = 'X'
				else:
					axis = 'Y'
				val = int(hex_val, 16)
				
				if active and ts is not None and last_event_ts is not None:
					dt = ts - last_event_ts
					if dt > self.inactivity_threshold:
						# flush previous gesture
						s_x, s_y = curr_start['X'], curr_start['Y']
						e_x, e_y = curr_end['X'], curr_end['Y']
						if all(v is not None for v in [s_x, s_y, e_x, e_y]):
							# use adb timestamp (last_event_ts) as the gesture timestamp
							ts_for_g = float(last_event_ts) if last_event_ts is not None else time.time()
							g = Gesture(int(s_x), int(s_y), int(e_x), int(e_y), ts_for_g)
							self.output_queue.put(g)
						
						# start a new gesture context
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
		
		# loop ended (process closed or stop requested) -> flush any active gesture
		if active:
			s_x, s_y = curr_start['X'], curr_start['Y']
			e_x, e_y = curr_end['X'], curr_end['Y']
			if all(v is not None for v in [s_x, s_y, e_x, e_y]):
				ts_for_g = float(last_event_ts) if last_event_ts is not None else time.time()
				g = Gesture(int(s_x), int(s_y), int(e_x), int(e_y), ts_for_g)
				self.output_queue.put(g)
	
	def run(self):
		# It's way more reliable than doing the detect simply using thread
		# why? probably my shitty threading code but this work so...
		asyncio.run(self._producer())
		
	def stop(self):
		self.__stop = True
		if self.__process:
			try:
				self.__process.terminate()
			except Exception:
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
