import queue
import re
import threading
import time
import math
import subprocess
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import List, Tuple
from AI.src.constants import logger

@dataclass
class Gesture:
    start_time: float
    end_time: float
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    points: List[Tuple[int, int]] = field(default_factory=list)
    is_finished: bool = True
    
    def __str__(self):
        dx = self.end_x - self.start_x
        dy = self.end_y - self.start_y
        dist = math.hypot(dx, dy)
        duration = (self.end_time - self.start_time) * 1000
        
        points_str = f"{self.points}"
        if len(self.points) > 10:
            points_str = f"[{self.points[0]}, ..., {self.points[-1]}] ({len(self.points)} items)"
        
        return (f"[⌚] {time.ctime(self.start_time)}\n"
                f"[⏱️] Duration: \t{duration:.0f} ms\n"
                f"[🏁] Start: \t[{self.start_x}, {self.start_y}]\n"
                f"[🏅] Finish:\t[{self.end_x}, {self.end_y}]\n"
                f"[📍] Points:\t{points_str}\n"
                f"[📐] Measured:\t[{dx}, {dy}] Dist: {dist:.2f}")


class GestureTracker(threading.Thread, AbstractContextManager):
    def __init__(self, output_queue: queue.Queue = queue.Queue(), live_feed: bool = False):
        super().__init__(daemon=True)
        self.output_queue = output_queue
        self.live_feed = live_feed
        self.__stop_event = threading.Event()
        self.__process = None
        
        self.__re_tracking = re.compile(r"ABS_MT_TRACKING_ID\s+([0-9a-f]+)")
        self.__re_btn = re.compile(r"BTN_TOUCH\s+(DOWN|UP)")
        self.__re_x = re.compile(r"ABS_MT_POSITION_X\s+([0-9a-f]+)")
        self.__re_y = re.compile(r"ABS_MT_POSITION_Y\s+([0-9a-f]+)")
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
        self.join()
    
    def run(self):
        cmd = ['adb', 'exec-out', 'getevent -lt']
        try:
            self.__process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL
            )
            
            active_touch = False
            curr_x, curr_y = None, None
            last_valid_x, last_valid_y = 0, 0
            gesture_points = []
            start_ts = 0.0
            
            for raw_line in iter(self.__process.stdout.readline, b''):
                if self.__stop_event.is_set():
                    break
                
                line = raw_line.decode('utf-8', errors='ignore').strip()
                if not line: continue
                
                now = time.time()
                update_coords = False
                
                match_x = self.__re_x.search(line)
                if match_x:
                    curr_x = int(match_x.group(1), 16)
                    last_valid_x = curr_x
                    update_coords = True
                
                match_y = self.__re_y.search(line)
                if match_y:
                    curr_y = int(match_y.group(1), 16)
                    last_valid_y = curr_y
                    update_coords = True
                
                if active_touch and update_coords:
                    if not gesture_points or gesture_points[-1] != (last_valid_x, last_valid_y):
                        gesture_points.append((last_valid_x, last_valid_y))
                        
                        if self.live_feed:
                            s_x, s_y = gesture_points[0]
                            live_g = Gesture(
                                start_time=start_ts, end_time=now,
                                start_x=s_x, start_y=s_y,
                                end_x=last_valid_x, end_y=last_valid_y,
                                points=list(gesture_points), is_finished=False
                            )
                            self.output_queue.put(live_g)
                
                is_start, is_end = False, False
                match_track = self.__re_tracking.search(line)
                if match_track:
                    if match_track.group(1) != "ffffffff":
                        is_start = True
                    else:
                        is_end = True
                
                match_btn = self.__re_btn.search(line)
                if match_btn:
                    if match_btn.group(1) == "DOWN":
                        is_start = True
                    elif match_btn.group(1) == "UP":
                        is_end = True
                
                if is_start and not active_touch:
                    active_touch = True
                    start_ts = now
                    gesture_points = [(last_valid_x, last_valid_y)]
                
                elif is_end and active_touch:
                    active_touch = False
                    if not gesture_points:
                        gesture_points.append((last_valid_x, last_valid_y))
                    
                    if gesture_points:
                        s_x, s_y = gesture_points[0]
                        e_x, e_y = gesture_points[-1]
                        
                        g = Gesture(
                            start_time=start_ts, end_time=now,
                            start_x=s_x, start_y=s_y,
                            end_x=e_x, end_y=e_y,
                            points=list(gesture_points), is_finished=True
                        )
                        self.output_queue.put(g)
                    curr_x, curr_y = None, None
        
        except Exception as e:
            pass
        finally:
            self.stop()
    
    def stop(self):
        self.__stop_event.set()
        if self.__process:
            try:
                self.__process.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    gesture_queue = queue.Queue()
    
    print("🤖 Tracker Active... (Press Ctrl+C to stop)")
    tracker = GestureTracker(gesture_queue)
    tracker.start()
    
    try:
        while True:
            try:
                gesture = gesture_queue.get(timeout=0.1)
                logger.info(f"\n{gesture}")
                logger.info("-" * 40)
            except queue.Empty:
                continue
    
    except KeyboardInterrupt:
        logger.info("\nExiting...")
        tracker.stop()
        tracker.join()