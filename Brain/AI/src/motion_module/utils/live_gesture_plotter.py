import queue
import re
import threading
import time
import subprocess
import argparse
from collections import deque
from typing import Tuple, Union
import matplotlib.pyplot as plt

from AI.src.motion_module.utils.gesture_tracker import GestureTracker
from AI.src.motion_module.utils.resources_utility import run_adb_screencap_to_memory

from AI.src.constants import logger

def get_screen_resolution() -> Tuple[int, int]:
    logger.info("📱 Querying device resolution from ADB...")
    try:
        out = subprocess.check_output(['adb', 'shell', 'wm', 'size']).decode('utf-8')
        matches = re.findall(r'size:\s*(\d+)x(\d+)', out)
        if matches:
            w, h = int(matches[-1][0]), int(matches[-1][1])
            logger.info(f"✅ Found resolution: {w}x{h}")
            return w, h
    except Exception as e:
        logger.info(f"⚠️ Failed to get resolution from ADB, defaulting to 1080x2400. ({e})")
    return 1080, 2400


class LiveGesturePlotter:
    """
    Will display in graphical form what's happening on the device.
    
    Parameters:
        gesture_queue: a queue that will be populated with Gesture objects
        max_history: maximum number of past gestures to keep
        base_alpha: if set to a float, it will be used as the base alpha for all gestures.
        log_console: if True, prints gesture details to the console
        live_screen: if True, overlays the gestures on top of a "live" ADB screen mirror
        width: width of the plot
        height: height of the plot
    """
    def __init__(self,
                 gesture_queue: queue.Queue,
                 max_history: int = 8,
                 base_alpha: Union[bool, float] = False,
                 log_console: bool = False,
                 live_screen: bool = False,
                 width: int = 1080,
                 height: int = 2400
        ):
        self.queue = gesture_queue
        self.width = width
        self.height = height
        self.base_alpha = base_alpha
        self.log_console = log_console
        self.live_screen = live_screen
        
        self.history = deque(maxlen=max_history)
        
        self.latest_finished_gesture = None
        self.active_live_gesture = None
        
        self.dynamic_artists = []
        
        self.latest_frame = None
        self.bg_image_artist = None
        self.screen_thread_running = False
    
    def _screen_updater(self):
        """
        Background thread fetching fast NumPy arrays directly into memory.
        """
        while self.screen_thread_running:
            try:
                # Drop in your fast custom function here
                img_array = run_adb_screencap_to_memory()
                
                if img_array is not None:
                    self.latest_frame = img_array
            
            except Exception as e:
                logger.error(f"Screen updater error: {e}")
                time.sleep(0.5) # 1/2 2 FPS, yeah I know this timer will not count the time spend drawing but it's a gimmick
    
    def run(self):
        logger.info("📊 Starting Live Plotter...")
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(5, 10))
        self.fig.canvas.manager.set_window_title("Live ADB Gestures")
        self._setup_axes()
        
        if self.live_screen:
            logger.info("🎥 Starting live screen capture...")
            self.screen_thread_running = True
            threading.Thread(target=self._screen_updater, daemon=True).start()
        
        plt.show()
        
        try:
            while plt.fignum_exists(self.fig.number):
                needs_redraw = False
                
                while not self.queue.empty():
                    try:
                        new_gesture = self.queue.get_nowait()
                        needs_redraw = True
                        
                        if new_gesture.is_finished:
                            if self.base_alpha is not False:
                                if self.latest_finished_gesture is not None:
                                    self._draw_gesture(
                                        self.latest_finished_gesture,
                                        alpha=float(self.base_alpha),
                                        is_permanent=True
                                    )
                                self.latest_finished_gesture = new_gesture
                            else:
                                # Standard finite mode
                                self.history.append(new_gesture)
                            
                            self.active_live_gesture = None
                            if self.log_console:
                                print(f"\n{new_gesture}\n" + "-" * 40)
                        else:
                            self.active_live_gesture = new_gesture
                    except queue.Empty:
                        break
                
                if self.live_screen and self.latest_frame is not None:
                    needs_redraw = True
                
                if needs_redraw:
                    self._update_plot()
                
                plt.pause(0.016)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.screen_thread_running = False
            plt.ioff()
            plt.close()
    
    def _setup_axes(self):
        self.ax.clear()
        self.ax.set_xlim(0, self.width)
        self.ax.set_ylim(self.height, 0)
        self.ax.set_title("Live Gesture Feed")
        self.ax.set_facecolor('#1e1e1e')
        self.fig.patch.set_facecolor('#121212')
        self.ax.tick_params(colors='white')
        self.ax.title.set_color('white')
        
        if self.live_screen:
            self.bg_image_artist = self.ax.imshow(
                [[[0, 0, 0]]], extent=[0, self.width, self.height, 0], aspect='auto', zorder=-1
            )
    
    def _draw_gesture(self, gesture, alpha, is_permanent=False):
        """Draws a gesture. If is_permanent is True, it is never added to the clear list."""
        dx = gesture.end_x - gesture.start_x
        dy = gesture.end_y - gesture.start_y
        is_tap = (dx ** 2 + dy ** 2) ** 0.5 < 50
        
        created_artists = []
        
        if is_tap:
            scatter = self.ax.scatter(
                gesture.start_x, gesture.start_y,
                color='cyan', s=100, alpha=alpha, edgecolors='white' if alpha > 0.5 else 'none'
            )
            created_artists.append(scatter)
        else:
            if gesture.points:
                xs = [p[0] for p in gesture.points]
                ys = [p[1] for p in gesture.points]
                line, = self.ax.plot(xs, ys, color='springgreen', linewidth=3, alpha=alpha)
                dot = self.ax.scatter(xs[-1], ys[-1], color='red', s=40, alpha=alpha)
                created_artists.extend([line, dot])
        
        if not is_permanent:
            self.dynamic_artists.extend(created_artists)
    
    def _update_plot(self):
        if self.live_screen and self.latest_frame is not None and self.bg_image_artist is not None:
            self.bg_image_artist.set_data(self.latest_frame)
            self.latest_frame = None
            
        for artist in self.dynamic_artists:
            try:
                artist.remove()
            except Exception:
                pass
        self.dynamic_artists.clear()
        
        if self.base_alpha is not False:
            if self.latest_finished_gesture and not self.active_live_gesture:
                self._draw_gesture(self.latest_finished_gesture, alpha=1.0, is_permanent=False)
        else:
            total = len(self.history)
            for i, gesture in enumerate(self.history):
                alpha = (i + 1) / total
                self._draw_gesture(gesture, alpha, is_permanent=False)
        
        if self.active_live_gesture:
            self._draw_gesture(self.active_live_gesture, alpha=1.0, is_permanent=False)
        
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    # Here is the ONLY place where print should exist, if we run this program as a module print should not exists,
    # we want to remove useless print to the terminal
    parser = argparse.ArgumentParser(description="Track and plot Android touches in real-time.")
    parser.add_argument("--subplots", type=int, default=8, help="Number of past gestures to keep")
    parser.add_argument("--keep-subplots", nargs='?', type=float, const=0.15, default=False,
                        help="Keep infinite history. Defaults to 0.15 opacity")
    parser.add_argument("--live-draw", action="store_true",  # Renamed from live-feed
                        help="Stream gestures as they happen")
    parser.add_argument("--live-screen", action="store_true",
                        help="Overlay the gestures on top of a live ADB screen mirror")
    parser.add_argument("--log-to-console", action="store_true", help="Print gesture details")
    args = parser.parse_args()
    
    dev_width, dev_height = get_screen_resolution()
    gesture_queue = queue.Queue()
    
    tracker = GestureTracker(gesture_queue, live_feed=args.live_draw)
    tracker.start()
    
    plotter = LiveGesturePlotter(
        gesture_queue=gesture_queue,
        max_history=args.subplots,
        base_alpha=args.keep_subplots,
        log_console=args.log_to_console,
        live_screen=args.live_screen,
        width=dev_width,
        height=dev_height
    )
    
    try:
        plotter.run()
    finally:
        tracker.stop()
        tracker.join()