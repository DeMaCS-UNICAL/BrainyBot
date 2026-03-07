import argparse
import queue
import threading
import time
from collections import deque
from typing import Union

import matplotlib.pyplot as plt
from AI.src.constants import logger
from AI.src.motion_module.utils.gesture_tracker import Gesture, GestureTracker
from AI.src.motion_module.utils.processed_phone_screen_data import (
    extract_phone_screen_info,
)
from AI.src.webservices.helpers import get_screenshot


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

    def __init__(
        self,
        gesture_queue: queue.Queue,
        max_history: int = 8,
        base_alpha: Union[bool, float] = False,
        log_console: bool = False,
        live_screen: bool = False,
        width: int = 1080,
        height: int = 2400,
    ):
        self.queue = gesture_queue
        self.width = width
        self.height = height
        self.base_alpha = base_alpha
        self.log_console = log_console
        self.live_screen = live_screen

        self.history = deque(maxlen=max_history)
        self.permanent_gestures = []

        self.latest_finished_gesture = None
        self.active_live_gesture = None

        self.latest_frame = None
        self.last_frame_drawn = None
        self.screen_thread_running = False

    def _screen_updater(self):
        """
        Background thread fetching fast NumPy arrays directly into memory.
        """
        while self.screen_thread_running:
            try:
                img_array = get_screenshot(to_memory=True)

                if img_array is not None:
                    self.latest_frame = img_array

            except Exception as e:
                logger.error(f"Screen updater error: {e}")
                time.sleep(0.5)

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
                                    self.permanent_gestures.append(
                                        self.latest_finished_gesture
                                    )
                                self.latest_finished_gesture = new_gesture
                            else:
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

                self.fig.canvas.flush_events()
                time.sleep(0.016)

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
        self.ax.set_facecolor("#1e1e1e")
        self.fig.patch.set_facecolor("#121212")
        self.ax.tick_params(colors="white")
        self.ax.title.set_color("white")

    def _draw_gesture(self, gesture: Gesture, alpha: float):
        """
        Draws a gesture, breaking the line if a phantom jump is detected.

        Parameters:
            gesture: The gesture to draw.
            alpha: The transparency of the gesture.
        """
        dx = gesture.end_x - gesture.start_x
        dy = gesture.end_y - gesture.start_y
        is_tap = (dx**2 + dy**2) ** 0.5 < 50

        if is_tap:
            self.ax.scatter(
                gesture.start_x,
                gesture.start_y,
                color="cyan",
                s=100,
                alpha=alpha,
                edgecolors="white" if alpha > 0.5 else "none",
            )
        else:
            if gesture.points:
                xs = []
                ys = []

                xs.append(gesture.points[0][0])
                ys.append(gesture.points[0][1])

                for i in range(1, len(gesture.points)):
                    # The commented part was an attempt to sanitize the data
                    # By removing unrealistic tap
                    # prev_x, prev_y = gesture.points[i - 1]
                    curr_x, curr_y = gesture.points[i]

                    # dist = ((curr_x - prev_x) ** 2 + (curr_y - prev_y) ** 2) ** 0.5
                    # if dist > 150:
                    #     xs.append(float("nan"))
                    #     ys.append(float("nan"))

                    xs.append(curr_x)
                    ys.append(curr_y)

                self.ax.plot(xs, ys, color="springgreen", linewidth=3, alpha=alpha)

                last_x, last_y = gesture.points[-1]
                self.ax.scatter(last_x, last_y, color="red", s=40, alpha=alpha)

    def _update_plot(self):
        self._setup_axes()

        if self.live_screen:
            frame_to_draw = (
                self.latest_frame
                if self.latest_frame is not None
                else self.last_frame_drawn
            )
            if frame_to_draw is not None:
                self.ax.imshow(
                    frame_to_draw,
                    extent=[0, self.width, self.height, 0],
                    aspect="auto",
                    zorder=-1,
                )
                if self.latest_frame is not None:
                    self.last_frame_drawn = self.latest_frame
                    self.latest_frame = None

        if self.base_alpha is not False:
            for gesture in self.permanent_gestures:
                self._draw_gesture(gesture, alpha=float(self.base_alpha))
            if self.latest_finished_gesture and not self.active_live_gesture:
                self._draw_gesture(self.latest_finished_gesture, alpha=1.0)
        else:
            total = len(self.history)
            for i, gesture in enumerate(self.history):
                alpha = (i + 1) / total
                self._draw_gesture(gesture, alpha)

        if self.active_live_gesture:
            self._draw_gesture(self.active_live_gesture, alpha=1.0)

        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Track and plot Android touches in real-time."
    )
    parser.add_argument(
        "--subplots", type=int, default=8, help="Number of past gestures to keep"
    )
    parser.add_argument(
        "--keep-subplots",
        nargs="?",
        type=float,
        const=0.15,
        default=False,
        help="Keep infinite history. Defaults to 0.15 opacity",
    )
    parser.add_argument(
        "--live-draw",
        action="store_true",
        help="Stream gestures as they happen",
    )
    parser.add_argument(
        "--live-screen",
        action="store_true",
        help="Overlay the gestures on top of a live ADB screen mirror",
    )
    parser.add_argument(
        "--log-to-console", action="store_true", help="Print gesture details"
    )
    args = parser.parse_args()

    data_x, data_y = extract_phone_screen_info()
    dev_width = int(data_x[1])
    dev_height = int(data_y[1])
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
        height=dev_height,
    )

    try:
        plotter.run()
    finally:
        tracker.stop()
        tracker.join()
