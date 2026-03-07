import datetime
import os
import pickle
import queue
from time import sleep

# External libraries
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from sklearn.linear_model import HuberRegressor, LinearRegression, RANSACRegressor
from sklearn.multioutput import MultiOutputRegressor

# Internal modules
from AI.src.constants import (
    CLIENT_PATH,
    MOTION_CALIBRATION_PATH,
    SCREENSHOT_PATH,
    TAPPY_ORIGINAL_SERVER_IP,
    logger,
)
from AI.src.motion_module.gesture_utils.gesture_tracker import GestureTracker
from AI.src.motion_module.utils.resources_utility import DoStuffElsewhere


class SwipeCalibrator:
    """
    A set of functions to generate a correction map for swipes to account for pen friction

    Parameters:
        method: "linear_regression" (default), "linear_interpolation", "ransac_regression", "huber_regression". Can be changed later.
    How to use:
        - Before calibrating the robot should be connected and on a screen that does not block adb captures (you can use npm calibration display)
        - The simplest calibration you can do simply implies running the program from a terminal with --save_to_file.
        - The --deep calibration will take a lot longer 11~ minutes but if the robot does not explode it will be way more precise
        - If you use the --deep calibration you also need --max_iterations and --target_error
        - You can add point to the calibration by using the --load_from_file and you method of calibration
        The manual calibration cannot be used to add point to a calibration since it's discarded if load_from_file is used
        - You can test the end result with --test and plot the graphs with --plot_{type}
        - ⚠️Remember to pass --save_to_file if you want to save the calibration, it will NOT do it by default
        - It's suggested to add a suffix with the name of the phone used for the calibration and to avoid sharing calibrations between devices
    """

    def __init__(self, method: str = "linear_regression"):
        self.is_trained = False
        self.cmds = []
        self.acts = []

        self.method = method
        self.model = None
        self.fallback_model = None

    def train(
        self,
        commanded_swipes: list[list[int]] = None,
        measured_swipes: list[list[int]] = None,
        method: str = None,
        drop_first: bool = False,
        outlier_zscore_threshold: float = None,
    ):
        """
        Train the model

        Parameters:
            commanded_swipes: A list of pairs (dx, dy) that the pen should have performed
            measured_swipes: A list of pairs (dx, dy) that the pen actually performed
            method: None (default, will use the one used in the class creation),
                "linear_regression", "linear_interpolation", "ransac_regression", "huber_regression"
            drop_first: if True, drop the first sample (useful if the first capture is noisy)
                example: the first we set [0, 0] = (0, 0) and we want to skip this
            outlier_zscore_threshold: remove measured samples with z-score > thresh (on measured magnitude)
                this tries to remove from the calibration garbage data
        Notes:
            - drop_first could be transformed in drop_selected: list[index]
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

        if outlier_zscore_threshold is not None and measured.shape[0] >= 3:
            mags = np.linalg.norm(measured, axis=1)
            m_mean = np.mean(mags)
            m_std = np.std(mags)
            if m_std > 0:
                z = (mags - m_mean) / m_std
                mask = np.abs(z) <= outlier_zscore_threshold
                if not np.all(mask):
                    logger.info(
                        f"Removing {np.sum(~mask)} outlier(s) from calibration data by z-score"
                    )
                    measured = measured[mask]
                    commanded = commanded[mask]

        if method is None:
            method = self.method

        if method == "linear_regression":
            self.model = LinearRegression()
            self.model.fit(measured, commanded)
        elif method == "huber_regression":
            self.model = MultiOutputRegressor(HuberRegressor())
            self.model.fit(measured, commanded)
        elif method == "ransac_regression":
            self.model = RANSACRegressor(LinearRegression(), random_state=0)
            self.model.fit(measured, commanded)
        elif method == "linear_interpolation":
            self.model = LinearNDInterpolator(measured, commanded)
            self.fallback_model = NearestNDInterpolator(measured, commanded)
        else:
            raise ValueError(f"Unknown calibration method: {method}")

        self.is_trained = True
        logger.info(f"Calibration complete using {self.method}.")

    def _predict(self, inputs):
        if self.method == "linear_interpolation":
            res = self.model(inputs)
            if np.any(np.isnan(res)):
                nans = np.isnan(res).any(axis=1)
                res[nans] = self.fallback_model(inputs[nans])
            return res
        return self.model.predict(inputs)

    def get_calibrated_command(self, target_dx, target_dy) -> tuple[float, float]:
        """
        transform the target displacement into the command needed to achieve it

        Returns:
            the [x, y] command needed to achieve the target swipe
        """
        if not self.is_trained:
            return target_dx, target_dy

        prediction = self._predict(np.array([[target_dx, target_dy]]))
        return prediction[0]

    def automatic_calibration(self):
        with GestureTracker() as tracker:
            # Get X data
            for i in range(2, 9):
                self.cmds.append([100 * i, 0])
                os.system(
                    f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {200 + 100 * i} {1000}'"
                )
                sleep(0.5)

            # Get X Half step
            for i in range(1, 9, 2):
                self.cmds.append([200 + 50 * i, 0])
                os.system(
                    f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {1000} {200 + 200 + 50 * i} {1000}'"
                )
                sleep(0.5)

            # Get Y data
            for i in range(2, 9):
                self.cmds.append([0, 100 * i])
                os.system(
                    f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {500} {200} {500} {200 + 100 * i}'"
                )
                sleep(0.5)

            # Get Y Half step
            for i in range(1, 9, 2):
                self.cmds.append([0, 200 + 50 * i])
                os.system(
                    f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {500} {200} {500} {200 + 200 + 50 * i}'"
                )
                sleep(0.5)

            # Get XY Data combined
            for i in range(2, 9):
                self.cmds.append([100 * i, 100 * i])
                os.system(
                    f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {200} {200 + 100 * i} {200 + 100 * i}'"
                )
                sleep(0.5)

            # Get XY Data combined Half step
            for i in range(1, 9, 2):
                self.cmds.append([200 + 50 * i, 200 + 50 * i])
                os.system(
                    f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {200} {200 + 200 + 50 * i} {200 + 200 + 50 * i}'"
                )
                sleep(0.5)

            queue_to_list = [
                tracker.output_queue.get(timeout=5)
                for _ in range(tracker.output_queue.qsize())
            ]
            for cmd, gesture in zip(self.cmds, queue_to_list):
                logger.info(gesture)
                logger.info(f"[🧪] ({cmd})")
                self.acts.append(
                    [gesture.end_x - gesture.start_x, gesture.end_y - gesture.start_y]
                )

    def deep_calibration(
        self,
        target: tuple[int, int],
        target_error: float = 0.1,
        max_iterations: int = 5,
    ):
        """
        Calibrate by setting an objective (600,0) and perform multiple actions until you get close to (600,0)
        Collects a lot of data, and it's slow

        Parameters:
            target: the target displacement [dx, dy]
            target_error: the target error percentage for each swipe
            max_iterations: the maximum number of iterations to perform for each swipe to get close to the target
        """

        with GestureTracker() as tracker:
            current_cmd = [target[0], target[1]]

            local_iterations = 0

            while True:
                os.system(
                    f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {500} {200 + int(current_cmd[0])} {500 + int(current_cmd[1])}'"
                )
                sleep(0.5)

                try:
                    gesture = tracker.output_queue.get(timeout=1)
                except queue.Empty:
                    logger.warning("No gesture detected!")
                    continue

                actual_dx = gesture.end_x - gesture.start_x
                actual_dy = gesture.end_y - gesture.start_y

                # Calculate error
                error_x = actual_dx - target[0]
                error_y = actual_dy - target[1]
                total_error = np.linalg.norm([error_x, error_y])
                target_mag = np.linalg.norm(target)
                error_percent = total_error / target_mag * 100
                logger.info(
                    f"\n{gesture}\n"
                    f"[🧪] Target:\t{target}\n"
                    f"[🚂] Command:\t{current_cmd}\n"
                    f"[⚠️] Error: \t[{error_x}, {error_y}] {total_error:.2f}px {error_percent:.2f}%"
                )

                self.cmds.append(list(current_cmd))
                self.acts.append([actual_dx, actual_dy])

                if total_error <= target_error * target_mag:
                    logger.info("Target reached within tolerance!")
                    break

                if local_iterations >= max_iterations:
                    logger.info("Max iterations reached for this target.")
                    break

                variant = 1.0
                """
                you can make it hover around the point with values > 1
                and you can make it more cautious with values < 1
                ⚠️ With values < 1 and > 1 it (most likely) will not get between tolerances
                so avoid setting max_iterations too high
                """
                current_cmd[0] += variant * (target[0] - actual_dx)
                current_cmd[1] += variant * (target[1] - actual_dy)

                local_iterations += 1

    def automatic_deep_calibration(
        self, target_error: float = 0.02, max_iterations: int = 5
    ):
        """
        ⚠️ Warning using value of x/y too small without moving on the other axis WILL result in the program crashing
        due to the inability of the GestureTracker to detect those movements!
        ⚠️ Warning movements too big will result in the pen going outside the display and breaking the calibration

        Parameters:
            target_error: the target error percentage for each swipe
            max_iterations: the maximum number of iterations to perform for each swipe to get close to the target
        """
        start_time = datetime.datetime.now()

        calibration_points = [
            (150, 0),
            (300, 0),
            (600, 0),
            (800, 0),
            (0, 150),
            (0, 300),
            (0, 600),
            (0, 800),
            (150, 150),
            (300, 300),
            (600, 600),
            (800, 800),
        ]

        for target in calibration_points:
            self.deep_calibration(
                target=target, target_error=target_error, max_iterations=max_iterations
            )

        finish_time = datetime.datetime.now()
        logger.info(f"Calibration took {finish_time - start_time}")

    def manual_calibration(self):
        """
        Add calibration point to the existing ones, can be used with an empty set of calibration points
        [⚠️ WARNING may damage the automatic_deep_calibration dataset ]
        You can use "clear_calibration" to remove all the calibration points
        """
        with GestureTracker() as tracker:
            try:
                while True:
                    taget_x = int(input("x: "))
                    taget_y = int(input("y: "))

                    self.cmds.append([taget_x, taget_y])

                    os.system(
                        f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {500} {200 + int(taget_x)} {500 + int(taget_y)}'"
                    )
                    sleep(1)

                    gesture = tracker.output_queue.get(timeout=2)
                    self.acts.append(
                        [
                            gesture.end_x - gesture.start_x,
                            gesture.end_y - gesture.start_y,
                        ]
                    )

                    logger.info(f"\n{gesture}\n[🧪]: {taget_x}, {taget_y}")
            except KeyboardInterrupt:
                pass  # redundant
            finally:
                pass

    def clear_calibration(self):
        self.cmds = []
        self.acts = []

    @staticmethod
    def _assemble_file_string_prefix(
        test_n: int = None,
        robot: str = "brainybot1",
        pen: str = "pinkyThing",
        suffix: str = None,
    ) -> str:
        match (test_n is None, suffix is None):
            case (True, True):
                return f"{robot}_{pen}"
            case (True, False):
                return f"{robot}_{pen}_{suffix}"
            case (False, True):
                return f"{test_n}_{robot}_{pen}"
            case (False, False):
                return f"{test_n}_{robot}_{pen}_{suffix}"

    def load_from_file(
        self,
        filename: str = None,
        test_n: int = None,
        robot: str = "brainybot1",
        pen: str = "pinkyThing",
        suffix: str = None,
    ):

        prefix = None
        if filename is None:
            prefix = self._assemble_file_string_prefix(test_n, robot, pen, suffix)
        else:
            if not filename.endswith(".pkl"):
                raise ValueError("File must be a pickle file")

        with DoStuffElsewhere(MOTION_CALIBRATION_PATH):
            if prefix is not None:
                for f in os.listdir():
                    if (
                        os.path.isfile(f)
                        and f.endswith(".pkl")
                        and f.startswith(prefix)
                    ):
                        filename = f
                        break

            with open(filename, "rb") as f:
                caricato = pickle.load(f)

        self.cmds = caricato["cmds"]
        self.acts = caricato["acts"]

    def save_to_file(
        self,
        filename: str = None,
        test_n: int = None,
        robot: str = "brainybot1",
        pen: str = "pinkyThing",
        suffix: str = None,
    ):
        if filename is None:
            filename = (
                f"{self._assemble_file_string_prefix(test_n, robot, pen, suffix)}.pkl"
            )

        if not filename.endswith(".pkl"):
            raise ValueError("File must be a pickle file")

        data_to_save = {"cmds": self.cmds, "acts": self.acts}

        with DoStuffElsewhere(MOTION_CALIBRATION_PATH):
            with open(filename, "wb") as f:
                pickle.dump(data_to_save, f)

    def plot_vector_calibration(self, max_range: int = 1000, plot_filename: str = None):
        """
        Generates the visualization of the calibration map with vectors

        Parameters:
            max_range: the max offset
            plot_filename: name of the plot
        """
        if not self.is_trained:
            raise ValueError("Train the model first!")

        grid_size = 10
        x, y = np.meshgrid(
            np.linspace(0, max_range, grid_size), np.linspace(0, max_range, grid_size)
        )

        flat_x, flat_y = x.flatten(), y.flatten()
        targets = np.column_stack((flat_x, flat_y))
        commands = self._predict(targets)

        plt.figure(figsize=(8, 6))
        # Plot the "push" vectors: (Command - Target)
        plt.quiver(
            flat_x,
            flat_y,
            commands[:, 0] - flat_x,
            commands[:, 1] - flat_y,
            color="blue",
            alpha=0.6,
            label="Correction Vector",
        )

        plt.title(
            f"Calibration Map: Required 'Push' to overcome Friction ({self.method})"
        )
        plt.xlabel("Desired X Displacement")
        plt.ylabel("Desired Y Displacement")
        plt.legend()
        plt.grid(True)
        if plot_filename is not None:
            with DoStuffElsewhere(SCREENSHOT_PATH):
                plt.savefig(plot_filename)
            logger.info(f"Plot saved to {plot_filename}")
        plt.show()

    def plot_heatmap_calibration(
        self, max_range: int = 1000, save_path: str | None = None
    ):
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
        x, y = np.meshgrid(x_linspace, y_linspace)

        flat_x, flat_y = x.flatten(), y.flatten()
        targets = np.column_stack((flat_x, flat_y))
        commands = self._predict(targets)

        # Calculate the magnitude of the correction vector (Command - Target)
        correction_vectors = commands - targets
        correction_magnitudes = np.linalg.norm(correction_vectors, axis=1)
        z = correction_magnitudes.reshape(x.shape)

        plt.figure(figsize=(10, 8))
        plt.pcolormesh(x, y, z, shading="auto", cmap="viridis")
        plt.colorbar(label="Correction Magnitude (pixels)")

        # Plot original training points if available (measured acts)
        if len(self.acts) > 0:
            acts_arr = np.array(self.acts)
            plt.plot(
                acts_arr[:, 0],
                acts_arr[:, 1],
                "ok",
                markersize=4,
                label="Measured Points",
            )
            plt.legend(loc="upper right")

        plt.title(f"Calibration Heatmap: Correction Magnitude ({self.method})")
        plt.xlabel("Desired X Displacement")
        plt.ylabel("Desired Y Displacement")
        plt.axis("equal")

        if save_path is not None:
            plt.savefig(save_path)
            logger.info(f"Heatmap saved to {save_path}")
        plt.show()

    def plot_connected_pairs(self, save_path: str | None = None):
        """
        Plots the commanded vs measured swipes connected by lines.
        This helps visualize the error for each specific training points

        Parameters:
            save_path: path to save the plot
        """
        if len(self.cmds) == 0 or len(self.acts) == 0:
            raise ValueError("No training data available to plot pairs")

        cmds_arr = np.array(self.cmds)
        acts_arr = np.array(self.acts)

        if len(cmds_arr) != len(acts_arr):
            logger.warning(
                "Commands and Acts arrays have different lengths, truncating to minimum"
            )
            min_len = min(len(cmds_arr), len(acts_arr))
            cmds_arr = cmds_arr[:min_len]
            acts_arr = acts_arr[:min_len]

        plt.figure(figsize=(10, 8))

        # What we wanted
        plt.scatter(
            cmds_arr[:, 0],
            cmds_arr[:, 1],
            c="blue",
            label="Commanded (Desired)",
            marker="o",
        )
        # What we got
        plt.scatter(
            acts_arr[:, 0],
            acts_arr[:, 1],
            c="red",
            label="Measured (Actual)",
            marker="x",
        )

        for i in range(len(cmds_arr)):
            plt.plot(
                [cmds_arr[i, 0], acts_arr[i, 0]],
                [cmds_arr[i, 1], acts_arr[i, 1]],
                "k-",
                alpha=0.3,
            )

        plt.title("Calibration: Commanded vs Measured Pairs")
        plt.xlabel("X Displacement")
        plt.ylabel("Y Displacement")
        plt.legend()
        plt.grid(True)
        plt.axis("equal")

        if save_path is not None:
            plt.savefig(save_path)
            logger.info(f"Pairs plot saved to {save_path}")
        plt.show()


if __name__ == "__main__":
    import argparse
    import sys

    # TAPPY_ORIGINAL_SERVER_IP = "http://127.0.0.1:8000"
    # CLIENT_PATH = "/home/wip/tesi/BrainyBot/tappy-client/clients/python"
    DESCRIPTION = """Run the calibration script
How to use:
    - Before calibrating the robot should be connected and on a screen that does not block adb captures (you can use npm calibration display)
    - The simplest calibration you can do simply implies running the program from a terminal with [--save_to_file].
    - The [--deep] calibration will take a lot longer 11~ minutes but if the robot does not explode it will be way more precise
    - If you use the [--deep] calibration you also need [--max_iterations] and [--target_error]
    - You can add point to the calibration by using the [--load_from_file] and you method of calibration
    The manual calibration cannot be used to add point to a calibration since it's discarded if [--load_from_file] is used
    - You can test the end result with [--test] and plot the graphs with [--plot_{type}]
    - ⚠️ Remember to pass [--save_to_file] if you want to save the calibration, it will NOT do it by default
    - It's suggested to add a suffix with the name of the phone used for the calibration and to avoid sharing calibrations between devices
"""

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "--method",
        type=str,
        default="linear_regression",
        help="Method to use for the calibration: linear_regression (default), linear_interpolation, ransac_regression, huber_regression",
    )
    parser.add_argument(
        "--manual", action="store_true", help="Choose the calibration swipes manually"
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Run the deep calibration (slow but more accurate)",
    )

    deep_required = "--deep" in sys.argv
    parser.add_argument(
        "--target_error",
        type=float,
        default=0.03,
        help="Target error for the deep calibration",
        required=deep_required,
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=5,
        help="Max iterations for the deep calibration",
        required=deep_required,
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="At the end of the execution let the user test the calibration",
    )

    parser.add_argument(
        "--load_from_file", action="store_true", help="Load the calibration from a file"
    )
    parser.add_argument(
        "--save_to_file", action="store_true", help="Save the calibration to a file"
    )
    parser.add_argument(
        "--plot_vector_calibration",
        action="store_true",
        help="Plot the vector calibration",
    )
    parser.add_argument(
        "--plot_heatmap_calibration",
        action="store_true",
        help="Plot the heatmap calibration",
    )
    parser.add_argument(
        "--plot_connected_pairs",
        action="store_true",
        help="Plot the commanded vs measured swipes connected by lines",
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default=None,
        help="A suffix to append to the calibration file name.",
    )
    parser.add_argument(
        "--robot", type=str, default="brainybot1", help="Name of the robot"
    )
    parser.add_argument("--pen", type=str, default="pinkyThing", help="Name of the pen")
    parser.add_argument(
        "--test_number", type=int, default=None, help="Test number prefix"
    )

    args = parser.parse_args()

    __cal = SwipeCalibrator(method=args.method)

    if args.load_from_file:
        try:
            __cal.load_from_file(
                suffix=args.suffix,
                robot=args.robot,
                pen=args.pen,
                test_n=args.test_number,
            )
            logger.info("Loaded calibration from file.")
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            sys.exit(1)

    if args.manual:
        logger.info("Starting manual calibration...")
        __cal.manual_calibration()
    elif args.deep:
        logger.info(
            f"Starting deep calibration (target_error={args.target_error}, max_iterations={args.max_iterations})..."
        )
        __cal.automatic_deep_calibration(
            target_error=args.target_error, max_iterations=args.max_iterations
        )
    elif not args.load_from_file:
        # Default to automatic calibration if no data loaded and no specific method selected
        logger.info("Starting automatic calibration...")
        __cal.automatic_calibration()

    if args.save_to_file:
        __cal.save_to_file(
            suffix=args.suffix, robot=args.robot, pen=args.pen, test_n=args.test_number
        )
        logger.info("Saved calibration to file.")

    if len(__cal.cmds) > 0 and len(__cal.acts) > 0:
        __cal.train()
    else:
        logger.warning("No calibration data available. Skipping training.")

    if args.plot_vector_calibration:
        __cal.plot_vector_calibration()

    if args.plot_heatmap_calibration:
        __cal.plot_heatmap_calibration()

    if args.plot_connected_pairs:
        __cal.plot_connected_pairs()

    if args.test:
        logger.info("Starting test mode...")
        with GestureTracker() as __tracker:
            try:
                while True:
                    try:
                        input_str = input("Enter target x,y (or q to quit): ")
                        if input_str.lower() == "q":
                            break
                        parts = input_str.replace(",", " ").split()
                        if len(parts) != 2:
                            logger.warning("Invalid input. Format: x,y")
                            continue

                        __taget_x = int(parts[0])
                        __taget_y = int(parts[1])
                    except ValueError:
                        logger.warning("Invalid numbers.")
                        continue

                    __cmd_needed = __cal.get_calibrated_command(__taget_x, __taget_y)

                    # Test swipe
                    os.system(
                        f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_IP} --light 'swipe {200} {500} {200 + int(__cmd_needed[0])} {500 + int(__cmd_needed[1])}'"
                    )
                    sleep(0.5)

                    try:
                        __gesture = __tracker.output_queue.get(timeout=2)
                        logger.info(
                            f"\n{__gesture}\n"
                            f"[🧪] Target:\t{__taget_x}, {__taget_y}\n"
                            f"[🚂] Command:\tX={__cmd_needed[0]:.2f}, Y={__cmd_needed[1]:.2f}"
                        )
                    except queue.Empty:
                        logger.warning("No gesture detected.")

            except KeyboardInterrupt:
                pass
            finally:
                logger.info("Exiting test mode...")
