import asyncio
import queue
import re
import threading
import time
from dataclasses import dataclass

from numpy.ma.core import sqrt


@dataclass  # Java to Kotlin: Watch what they need to imitate a FRACTION of our power
class Gesture:
	start_x: int
	start_y: int
	end_x: int
	end_y: int
	timestamp: float


class GestureTracker(threading.Thread):
	def __init__(self, output_queue):
		super().__init__(daemon=True)
		self.output_queue = output_queue
		# You could add other stuff like finger touchdown and so on... it's out of my scope tough
		self.pattern = re.compile(r"ABS_MT_POSITION_(X|Y)\s+([0-9a-f]+)")
		self.__stop = False
	
	async def _producer(self):
		process = await asyncio.create_subprocess_exec('adb', 'shell', 'getevent', '-lt',
		                                               stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
		
		curr_start = {'X': None | int | str, 'Y': None | int | str}
		curr_end = {'X': None | int | str, 'Y': None | int | str}
		active = False
		
		while not self.__stop:
			try:
				line_bytes = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
				if not line_bytes: break
				
				match = self.pattern.search(line_bytes.decode())
				if match:
					axis, hex_val = match.groups()
					val = int(hex_val, 16)
					
					if not active:
						active = True
						curr_start = {'X': None, 'Y': None}
					
					if curr_start[axis] is None:
						curr_start[axis] = val
					curr_end[axis] = val
			
			except asyncio.TimeoutError:
				if active:
					s_x, s_y = curr_start['X'], curr_start['Y']
					e_x, e_y = curr_end['X'], curr_end['Y']
					
					if all(v is not None for v in [s_x, s_y, e_x, e_y]):
						# noinspection PyTypeChecker
						g = Gesture(int(s_x), int(s_y), int(e_x), int(e_y), time.time())
						self.output_queue.put(g)
					
					active = False
					curr_start = {'X': None, 'Y': None}
	
	def run(self):
		# It's way more reliable than doing the detect simply using thread
		# why? probably my shitty threading code but this work so...
		asyncio.run(self._producer())
		
	def stop(self):
		self.__stop = True


if __name__ == "__main__":
	gesture_queue = queue.Queue()
	
	tracker = GestureTracker(gesture_queue)
	tracker.start()
	
	print("🔫... Non c'è l'emoji del fischietto")
	
	try:
		while True:
			try:
				gesture = gesture_queue.get(timeout=0.1)
				print(f"\n[⌚] {time.ctime(gesture.timestamp)}")
				print(f"[🏁] ({gesture.start_x}, {gesture.start_y})")
				print(f"[🎖️] ({gesture.end_x}, {gesture.end_y})")
				print(f"[📐] ({gesture.end_x - gesture.start_x}, {gesture.end_y - gesture.start_y}, {sqrt((gesture.end_x - gesture.start_x) ** 2 + (gesture.end_y - gesture.start_y) ** 2)})")
			
			except queue.Empty:
				continue

	except KeyboardInterrupt:
		print("\nExiting...")
