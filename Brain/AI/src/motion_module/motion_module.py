# Internal libraries
import os
import threading
from collections import Counter

# Python
import mahotas
import math
import numpy as np
# External libraries
from PIL import ImageDraw, Image

from AI.src.constants import logger, TAPPY_ORIGINAL_SERVER_PROTOCOL, TAPPY_ORIGINAL_SERVER_PORT, \
    TAPPY_ORIGINAL_SERVER_IP, CLIENT_PATH
from AI.src.motion_module.enums import MotionType, Towards
from AI.src.motion_module.utils.image_processing_utility import to_int32, apply_mask_make_transparent, calculate_offset
from AI.src.motion_module.utils.pen_calibration import SwipeCalibrator
from AI.src.motion_module.utils.resources_utility import run_adb_screencap_to_memory


class Worker(threading.Thread):
    def __init__(self, target, args=()):
        super().__init__()
        self.target = target
        self.args = args
    
    def run(self):
        self.target(*self.args)


class MotionModule:
    """
    Parameters:
        ui_mask: an image or a ndArray representing the mask of the UI you want to interact with.
        swipe_calibrator: Used to correct some error of the pointing device, you can omit it.
            The swipe calibrator (if provided) need to be already trained.
        motion_type: the type of motion you want to use, default is swipe.
        force_headless: if True the module will use adb for movements.
        start_position: where you start (will also expand the desk to fit your position)
    How to use:
        - To properly use the motion module you should implement in you application a set of actions
        - When the motion module moves it fills the desk with the (screenshot - the mask) at your position
        - When you want to scan it with cv2 or other method you can request the desk with 'get_desk_copy' or 'get_pil_desk'
        - If you want to clear the whole map and scan it from scratch you can call 'clear_desk'
        - If your position no longer matches the one accounted for by the module you can reset it with 'set_current_position' but you may want to 'collapse_desk' after
        - When you want to (tap 1000, 1000) do not go to (1000, 1000) use 'goto_for_action' and execute the action at the returned value
    """
    
    def __init__(
            self,
            ui_mask: Image.Image | np.ndarray,
            swipe_calibrator: SwipeCalibrator,
            motion_type: MotionType = MotionType.SWIPE,
            image_history_size: int = 10,
            force_headless: bool = False,
            start_position: tuple[int, int] = (0, 0),
    ):
        match isinstance(ui_mask, Image.Image):
            case True:
                self._ui_mask: np.ndarray = to_int32(ui_mask)
            case False:
                self._ui_mask: np.ndarray = ui_mask
        height, width = self._ui_mask.shape[:2]
        # array RGBA trasparente (0 = trasparente)
        self._desk = np.zeros((height, width, 4), dtype=np.uint8)
        self._desk_offset = start_position
        self._expand_desk(start_position, (width, height))
        self.swipe_calibrator = swipe_calibrator
        self._position: tuple[int, int] = start_position
        self._positions_history: list[tuple[int, int]] = []
        self._frames_history: list[np.ndarray] = []
        self._frame_history_size: int = image_history_size
        self._motion_type: MotionType = motion_type
        self._motion_area: tuple[tuple[int, int], tuple[int, int]] | None = None
        if motion_type == MotionType.SWIPE:
            self.calculate_motion_area()
        self._force_headless = force_headless
    
    # TODO: add a way to auto-train the swipe calibrator
    # TODO: add confidence threshold to have some kind of security net for wrong movement, and a correction for them
    # TODO: move then estimate movement, and recalculate next movements
    # TODO: merge images at correct angles/offset between them
    # TODO: keep track of where we are regarding an initial position
    # TODO: a function to reset the position
    # TODO: a function to check and explore the map boundaries
    # TODO: a function to define the motion area from the mask
    
    @staticmethod
    def _angle_to_offset(distance: float, angle: float):
        return np.cos(angle) * distance, np.sin(angle) * distance
    
    def _expand_desk(self, coordinates: tuple[int, int], size: tuple[int, int]):
        """
        Expands the desk to include the area defined by the coordinates (x, y) and the dimensions (width, height).
        Parameters:
            coordinates: x, y of the top-left corner of the area.
            size: width, height of the area.
        """
        current_pos = np.array(self._desk_offset)
        # shape is (h, w) but we all know that (w, h) is superior so flip it
        current_size = np.array(self._desk.shape[:2][::-1])
        
        new_pos = np.array(coordinates)
        new_size = np.array(size)
        
        min_coords = np.minimum(current_pos, new_pos)
        max_coords = np.maximum(current_pos + current_size, new_pos + new_size)
        
        offset = current_pos - min_coords
        
        if np.any(offset > 0) or np.any(max_coords > current_pos + current_size):
            new_dims = max_coords - min_coords
            new_w, new_h = new_dims
            new_desk = np.zeros((new_h, new_w, 4), dtype=np.uint8)
            
            # For readability... if you prefer replace everything with 0 and 1 and talk to me later
            offset_x, offset_y = offset
            current_w, current_h = current_size
            
            new_desk[offset_y: offset_y + current_h, offset_x: offset_x + current_w] = self._desk
            
            self._desk = new_desk
            self._desk_offset = tuple(min_coords)
    
    def _add_frame_to_desk(self, frame: np.ndarray, coordinates: tuple[int, int]):
        """
        Paste a frame on the desk, ignoring irrelevant areas.
        Parameters:
            frame: the frame to paste, as a numpy array.
            coordinates: the coordinates of the top-left corner of the frame, in pixels (x, y).
        """
        masked_frame = apply_mask_make_transparent(frame, self._ui_mask).astype(
            np.uint8
        )
        w, h = masked_frame.shape[:2][::-1]
        x, y = coordinates
        
        self._expand_desk((x, y), (w, h))
        
        desk_x = x - self._desk_offset[0]
        desk_y = y - self._desk_offset[1]
        
        mask = masked_frame[:, :, 3] > 0
        self._desk[desk_y: desk_y + h, desk_x: desk_x + w][mask] = masked_frame[mask]
    
    def _add_last_frame_to_desk(self):
        """
        Paste the last frame from the history on the desk.
        """
        self._add_frame_to_desk(self._frames_history[-1], coordinates=self._position)
    
    def _majority_offset_calculation(self):
        """
        Calculates the offset between the last two frames in the history, using the UI mask to ignore irrelevant areas.
        This variant execute different algorithm and takes the best / most common result.
        """
        # TODO: Could make this multithreaded
        results = []
        
        for i in range(3):
            results.append(calculate_offset(
                self._frames_history[-2],
                self._frames_history[-1],
                self._ui_mask,
                used_detector=i,
            ))
        
        votes = [(round(r[0]), round(r[1])) for r in results]
        most_common = Counter(votes).most_common(1)[0][0]
        dx, dy, confidence = max([r for r in results if (round(r[0]), round(r[1])) == most_common], key=lambda x: x[2])
        logger.debug(f"dx = {dx}, dy = {dy}, confidence = {confidence}")
        return dx, dy, confidence
    
    def _calculate_offset(self, detector: int = 1) -> tuple[float, float, float]:
        """
        Calculates the offset between the last two frames in the history, using the UI mask to ignore irrelevant areas.
        """
        dx, dy, confidence = calculate_offset(
            self._frames_history[-2],
            self._frames_history[-1],
            self._ui_mask,
            used_detector=detector,
        )
        logger.debug(f"dx = {dx}, dy = {dy}, confidence = {confidence}")
        return dx, dy, confidence
    
    def calculate_motion_area(self, borders: int = 10):
        """
        Parameters:
            borders: the distance we want to maintain from the border of the mask
        https://www.geeksforgeeks.org/dsa/largest-rectangular-area-in-a-histogram-using-stack/
        """
        
        # Could be made protected/private
        # TODO: Could optimize the motion area for vertical and horizontal movement instead of "biggest one"
        
        if self._ui_mask.ndim == 3:
            binary_mask = self._ui_mask[:, :, 3] != 0
        else:
            binary_mask = self._ui_mask != 0
        
        distance_map = mahotas.distance(binary_mask)
        valid_region = distance_map > borders
        
        rows, cols = valid_region.shape
        heights = np.zeros(cols, dtype=np.int32)
        max_area = 0
        best_rect = ((0, 0), (0, 0))
        
        for r in range(rows):
            heights = np.where(valid_region[r], heights + 1, 0)
            stack = [-1]
            for c in range(cols + 1):
                h = heights[c] if c < cols else 0
                while stack[-1] != -1 and heights[stack[-1]] >= h:
                    height = heights[stack.pop()]
                    width = c - stack[-1] - 1
                    area = height * width
                    if area > max_area:
                        max_area = area
                        best_rect = ((stack[-1] + 1, r - height + 1), (c, r + 1))
                stack.append(c)
        
        self._motion_area = best_rect
    
    def _offset_to_swipe(self, offset: tuple[int, int]) -> tuple[int, int, int, int] | None:
        """
        Converts a desired offset into swipe coordinates based on the motion area.
        Parameters:
            offset: the desired offset, in pixels (x, y).
        Returns:
            start_x, start_y, end_x, end_y || None if the offset is out of bounds.
        """
        if self._motion_area is None:
            self.calculate_motion_area()
        
        (min_x, min_y), (max_x, max_y) = self._motion_area
        
        area_width = max_x - min_x
        area_height = max_y - min_y
        
        target_x, target_y = offset
        
        if abs(target_x) > area_width or abs(target_y) > area_height:
            logger.info(
                f"Desired offset {offset} is out of bounds for the motion area."
            )
            return None
        
        # Center the swipe vector in the available space (kinda works)
        # start_x = (min_x + max_x - target_x) // 2 # <- +x ; -> -x
        start_x = (min_x + max_x + target_x) // 2  # <- -x ; -> +x
        start_y = (min_y + max_y + target_y) // 2
        
        # end_x = start_x + target_x # <- +x ; -> -x
        end_x = start_x - target_x  # <- -x ; -> +x
        end_y = start_y - target_y
        
        return int(start_x), int(start_y), int(end_x), int(end_y)
    
    @staticmethod
    def __swipe_adb(start_x: int, start_y: int, end_x: int, end_y: int):
        os.system(f"adb shell input swipe {start_x} {start_y} {end_x} {end_y}")
    
    @staticmethod
    def __swipe_robot(start_x: int, start_y: int, end_x: int, end_y: int):
        os.system(
            f"python3 {CLIENT_PATH}/client3.py --url {TAPPY_ORIGINAL_SERVER_PROTOCOL}://{TAPPY_ORIGINAL_SERVER_IP}:{TAPPY_ORIGINAL_SERVER_PORT} --light 'swipe {start_x} {start_y} {end_x} {end_y}'"
        )
    
    def _swipe(self, start_x: int, start_y: int, end_x: int, end_y: int):
        if self._force_headless:
            return self.__swipe_adb(start_x, start_y, end_x, end_y)
        return self.__swipe_robot(start_x, start_y, end_x, end_y)
    
    def _clamp_frame_history(self, keep: int = None):
        if keep is None:
            keep = self._frame_history_size
        self._frames_history = self._frames_history[-keep:]
    
    def _ensure_history(self):
        """
        Make sure there are at least one frame in the history, so we can calculate the offset.
        """
        if len(self._frames_history) < 2:
            self._positions_history.append(self._position)
            self._frames_history.append(
                run_adb_screencap_to_memory(
                    save_file=f"test_{len(self._frames_history)}.png"
                )
            )
            self._add_last_frame_to_desk()
    
    @staticmethod
    def distance(point_a: tuple[int, int], point_b: tuple[int, int]) -> float:
        return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5
    
    def move_with_offset(self, offset: tuple[int, int]) -> tuple[float, float] | None:
        """
        Tries to move the map ONCE by swiping
        Parameters:
            offset: int(x), int(y), how much you want to move, DO NOT pre-calibrate these values
        Returns:
            offset_x, offset_y || None if something went wrong
        """
        self._ensure_history()
        command = self.swipe_calibrator.get_calibrated_command(*offset)
        command = int(command[0]), int(command[1])
        swipe = self._offset_to_swipe(command)
        if swipe is None:
            # Note: here you should NOT retry with multiple swipes command, the move command should only do ONE action
            return None
        self._swipe(*swipe)
        
        self._frames_history.append(
            run_adb_screencap_to_memory(
                save_file=f"test_{len(self._frames_history)}.png"
            )
        )
        # dx, dy, confidence = self._calculate_offset()
        dx, dy, confidence = self._majority_offset_calculation()
        self._position = (self._position[0] - int(dx), self._position[1] - int(dy))
        self._positions_history.append(self._position)
        self._add_last_frame_to_desk()
        self._clamp_frame_history()
        
        return dx, dy
    
    def move_with_angle(self, distance: float, angle: float) -> tuple[float, float] | None:
        """
        Tries to move the map ONCE by swiping
        Parameters:
            distance: how far you want to move, in pixels
            angle: the angle you want to move, in radians
        Returns:
            offset_x, offset_y: None if something went wrong
        """
        self._ensure_history()
        # TODO: may need to invert (*-1) angle_to_offset result to have it match the screen coordinates
        return self.move_with_offset(self._angle_to_offset(distance, angle))
    
    def move_with_time(self):
        """
        Tries to move the map ONCE by pressing for x time on a point
        """
        self._ensure_history()
        # TODO: to implement
        """
        The problem with this function is the press may become faster exponentially and cap at some point
        We need to have an approximation of fun(time) = movement
        So another calibration step
        """
        pass
    
    def move_with_tap(self, towards: Towards):
        """
        Tries to move the map ONCE by tapping on a point
        Parameters:
            The direction we want to move to
        Returns:
            ???
        """
        # TODO: to implement
        """
        The problem with this function is that a tap may move a fixes amount or a full screen
        it need to be set prior to moving and for each game
        """
        pass
    
    def goto(
            self,
            destination: tuple[int, int],
            acceptable_distance: float = 50,
            cutoff_distance: float = 10.0,
    ) -> tuple[int, int]:
        """
        Goes to an absolute destination
        Parameters:
            destination: the absolute destination, in pixels (x, y)
            acceptable_distance: the maximum distance from the destination we are willing to accept
            cutoff_distance: the minimum average distance from the destination we need to maintain in the last 3 moves
                to keep trying, to avoid infinite loops when we're stuck
        Returns:
            The distance moved from the starting position, in pixels (x, y)
        """
        
        if self._motion_area is None:
            # It's redundant because at this point should be already instantiated, but I feel safer
            self.calculate_motion_area()
        
        # min - max
        max_x_movement = abs(self._motion_area[0][0] - self._motion_area[1][0])
        max_y_movement = abs(self._motion_area[0][1] - self._motion_area[1][1])
        
        movement_history = []
        delta_history: list[tuple[float, float]] = []
        while (
                (dist := self.distance(self._position, destination)) > acceptable_distance
        ) and (
                len(movement_history) < 3
                or np.mean(movement_history[-3:]) > cutoff_distance
        ):
            logger.debug(f"Distance to destination: {dist}")
            
            x_distance = destination[0] - self._position[0]
            y_distance = destination[1] - self._position[1]
            
            clamped_x = int(
                max(-(max_x_movement // 2), min((max_x_movement // 2), x_distance))
            )
            clamped_y = int(
                max(-(max_y_movement // 2), min((max_y_movement // 2), y_distance))
            )
            
            movement = (clamped_x, clamped_y)
            
            dx, dy = self.move_with_offset(movement)
            delta_history.append((dx, dy))
            movement_history.append(np.linalg.norm(dx - dy))
        
        return sum([round(x[0]) for x in delta_history]), sum([round(y[1]) for y in delta_history])
    
    def goto_for_action(self, desired_center: tuple[int, int]) -> tuple[int, int] | None:
        """
        Move the map to that your "Action" can be set in the middle of the screen
        If it cannot do it will return None, otherwise it will return the position where you should execute the action
        Parameters:
            desired_center: the destination where you want to set your "Action" button, in pixels (x, y) (map coordinates)
            maximum_distance: the maximum distance from the destination we are willing to accept
        Returns:
            the final screen coordinates where you should execute the action, in pixels (x, y) || None if it failed
        """
        if self._motion_area is None:
            self.calculate_motion_area()

        height, width = self._ui_mask.shape[:2]
        center_screen_x = width // 2
        center_screen_y = height // 2
        
        # actual_position_x, actual_position_y = self._position
        # actual_center_x, actual_center_y = (actual_position_x + center_screen_x, actual_position_y + center_screen_y)
        
        desired_center_x, desired_center_y = desired_center
        desired_position_x, desired_position_y = (desired_center_x - center_screen_x,
                                                  desired_center_y - center_screen_y)
        
        distance = self.goto((desired_position_x, desired_position_y))
        if distance is None:
            return None
        
        final_screen_x = desired_center_x - self._position[0]
        final_screen_y = desired_center_y - self._position[1]
        
        if not (0 <= final_screen_x <= width and 0 <= final_screen_y <= height):
            return None
        
        # final_position_x, final_position_y = self._position
        # final_position_error_x, final_position_error_y = (desired_position_x - final_position_x,
        #                                                   desired_position_y - final_position_y)
        # final_center_x, final_center_y = (center_screen_x - final_position_error_x,
        #                                   center_screen_y - final_position_error_y)
        
        return final_screen_x, final_screen_y
    
    def get_pil_desk(self) -> Image.Image:
        return Image.fromarray(self._desk, mode="RGBA")
    
    def get_desk_copy(self) -> np.ndarray:
        return self._desk.copy()
    
    def clear_desk(self):
        """
        Makes every pixel transparent as it started
        Use this if you do not want anything of the old scan
        ⚠️This will not reset the position, goto(0,0) before doing this
        ⚠️This will clear the frame_history
        """
        self._desk = np.zeros_like(self._desk)
        self._frames_history.clear()
    
    def position(self) -> tuple[int, int]:
        """
        Returns:
            the current position, in pixels (x, y)
        """
        return self._position
    
    def set_current_position(self, position: tuple[int, int]):
        """
        Will set the current position without adding frames to the desk
        ⚠️If you're not sure about where you are do not use this function!
        Parameters:
            position: the new position, in pixels (x, y)
        """
        self._position = position
        self._desk_offset = position
        
    def collapse_desk(self):
        """
        Will clear the desk and resize to the minimum size for the actual position starting from (0, 0)
        """
        height, width = self._ui_mask.shape[:2]
        self._desk = np.zeros((height, width, 4), dtype=np.uint8)
        self._desk_offset = self._position
        self._expand_desk(self._position, (width, height))


class TestMotionModule(MotionModule):
    def test_draw_largest_bbox(self, output_path: str = "bbox_output.png"):
        """
        you will never guess what this does
        """
        self.calculate_motion_area()
        if self._motion_area is not None:
            (x1, y1), (x2, y2) = self._motion_area
            logger.debug(f"Bounding Box found: {self._motion_area}")
            img = Image.fromarray(self._ui_mask.astype(np.uint8))
            draw = ImageDraw.Draw(img)
            draw.rectangle(
                [x1, y1, x2 - 1, y2 - 1], fill="green", outline="red", width=5
            )
            img.save(output_path)
            logger.debug(f"Image saved to {output_path}")
        else:
            logger.debug("No bounding box calculated.")


if __name__ == "__main__":
    import argparse
    
    argparser = argparse.ArgumentParser()
    
    logger.debug(os.getcwd())
    
    cal = SwipeCalibrator()
    # cal.load()
    # cal.train()
    # cal.plot_calibration()
    
    motion_module = MotionModule(
        ui_mask=Image.open("resources/p10lite/islandempire_mask_alpha.png").convert(
            "RGBA"
        ),
        swipe_calibrator=cal,
        force_headless=True,
    )
    
    logger.debug(motion_module.goto((2000, 0)))
    motion_module.move_with_offset((0, 500))
    logger.debug(motion_module.position())
    logger.debug(motion_module.goto((0, 0)))
    
    print(motion_module.position())
    Image.fromarray(motion_module._desk).save("utils/desk2.png")
# motion_module.test_draw_largest_bbox()

# from matplotlib import pyplot as plt
# md = OldMotionModule(
#     image_mask=Image.open("resources/islandempire_mask_alpha.png"),
#     screen_size=(1080, 2340)
# )
# desk = Image.new("RGBA", (3000, 3000), (255, 0, 0))
# # logger.debug(
# #     md.move(
# #         step_number = (12, 5),
# #         destination_offset= (1200, 500),
# #         desk = desk
# #     )
# # )
# # )
# logger.debug(md.calculate_map_size())
# plt.imshow(desk)
# plt.show()
