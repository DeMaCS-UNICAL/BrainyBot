import os
import threading
import time
import tkinter as tk

# External libraries
import customtkinter
import numpy as np
from customtkinter import filedialog
from PIL import Image, ImageTk

# Internal modules
from AI.src.constants import MOTION_MODULE
from AI.src.motion_module.motion_module import MotionModule
from AI.src.motion_module.swipe_calibrator import SwipeCalibrator
from AI.src.webservices.helpers import get_screenshot


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Controllable Motion Module")
        self.geometry("1600x900")
        customtkinter.set_default_color_theme("dark-blue")
        customtkinter.set_appearance_mode("dark")  # dark theme supremacy

        dummy_mask = np.ones((2340, 1080, 4), dtype=np.uint8) * 255
        self.motion_module = MotionModule(
            ui_mask=dummy_mask, swipe_calibrator=SwipeCalibrator(), force_headless=True
        )

        # Configure grid layout
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Left frame for phone screen
        self.left_frame = customtkinter.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.screen_label = customtkinter.CTkLabel(self.left_frame, text="Live Feed")
        self.screen_label.pack(padx=10, pady=5)

        self.image_label = customtkinter.CTkLabel(self.left_frame, text="")
        self.image_label.pack(padx=10, pady=5)
        self.image_label.bind("<Button-1>", self.on_screen_click)

        # Middle frame for Desk
        self.desk_frame = customtkinter.CTkFrame(self)
        self.desk_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.desk_title_label = customtkinter.CTkLabel(
            self.desk_frame, text="Desk (Map)"
        )
        self.desk_title_label.pack(padx=10, pady=2)

        self.desk_canvas = tk.Canvas(
            self.desk_frame, bg="#212121", highlightthickness=0
        )
        self.desk_canvas.pack(fill="both", expand=True)

        self.desk_canvas.bind("<ButtonPress-1>", self.on_desk_press)
        self.desk_canvas.bind("<B1-Motion>", self.on_desk_drag)
        self.desk_canvas.bind("<ButtonRelease-1>", self.on_desk_release)

        self.desk_image_item = None
        self.desk_pil_image = None
        self.desk_tk_image = None
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        self.desk_scale = 2

        self.screen_update_interval = 1.0
        self.desk_update_interval = 2.0

        # Right frame for controls
        self.right_frame = customtkinter.CTkFrame(self)
        self.right_frame.grid(row=0, column=2, padx=10, pady=10, sticky="ns")

        self.control_label = customtkinter.CTkLabel(
            self.right_frame,
            text="Controls",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.control_label.pack(padx=10, pady=10)

        self.__standard_input_group()
        self.__movement_group()
        self.__position_and_desk_group()
        self.__configuration_group()
        self.__extra_group()

        self.position_label = customtkinter.CTkLabel(
            self.right_frame,
            text="Position: (0, 0)",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        self.position_label.pack(side="bottom", padx=10, pady=10)

        self.status_label = customtkinter.CTkLabel(
            self.right_frame, text="Status: Idle", wraplength=200
        )
        self.status_label.pack(side="bottom", padx=10, pady=10)

        # Start live feed thread
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.live_feed_loop, daemon=True)
        self.thread.start()

        # Start desk update thread
        self.desk_thread = threading.Thread(target=self.desk_update_loop, daemon=True)
        self.desk_thread.start()

    def __standard_input_group(self):
        self.input_frame = customtkinter.CTkFrame(self.right_frame)
        self.input_frame.pack(padx=10, pady=10, fill="x")

        self.label_x = customtkinter.CTkLabel(self.input_frame, text="X, dX:")
        self.label_x.grid(row=0, column=0, padx=5, pady=5)
        self.entry_x = customtkinter.CTkEntry(self.input_frame, width=100)
        self.entry_x.grid(row=0, column=1, padx=5, pady=5)
        self.entry_x.insert(0, "0")

        self.label_y = customtkinter.CTkLabel(self.input_frame, text="Y, dY:")
        self.label_y.grid(row=1, column=0, padx=5, pady=5)
        self.entry_y = customtkinter.CTkEntry(self.input_frame, width=100)
        self.entry_y.grid(row=1, column=1, padx=5, pady=5)
        self.entry_y.insert(0, "0")

    def __movement_group(self):
        self.group1_label = customtkinter.CTkLabel(
            self.right_frame,
            text="Movement",
            font=customtkinter.CTkFont(size=14, weight="bold"),
        )
        self.group1_label.pack(padx=10, pady=(15, 5))

        self.btn_goto = customtkinter.CTkButton(
            self.right_frame, text="Goto(x, y)", command=self.cmd_goto
        )
        self.btn_goto.pack(padx=20, pady=5, fill="x")

        self.btn_goto_action = customtkinter.CTkButton(
            self.right_frame, text="Goto For Action(x, y)", command=self.cmd_goto_action
        )
        self.btn_goto_action.pack(padx=20, pady=5, fill="x")

        self.btn_move = customtkinter.CTkButton(
            self.right_frame, text="Move(dx, dy)", command=self.cmd_move
        )
        self.btn_move.pack(padx=20, pady=5, fill="x")

    def __position_and_desk_group(self):
        self.group2_label = customtkinter.CTkLabel(
            self.right_frame,
            text="Position & Desk",
            font=customtkinter.CTkFont(size=14, weight="bold"),
        )
        self.group2_label.pack(padx=10, pady=(15, 5))

        self.btn_check_pos = customtkinter.CTkButton(
            self.right_frame,
            text="Check Position Changed",
            command=self.cmd_check_position,
        )
        self.btn_check_pos.pack(padx=20, pady=5, fill="x")

        self.btn_set_pos = customtkinter.CTkButton(
            self.right_frame, text="Set Position(x, y)", command=self.cmd_set_position
        )
        self.btn_set_pos.pack(padx=20, pady=5, fill="x")

        self.btn_collapse = customtkinter.CTkButton(
            self.right_frame, text="Collapse Desk", command=self.cmd_collapse_desk
        )
        self.btn_collapse.pack(padx=20, pady=5, fill="x")

        self.btn_reset_desk = customtkinter.CTkButton(
            self.right_frame, text="Reset Desk", command=self.cmd_reset_desk
        )
        self.btn_reset_desk.pack(padx=20, pady=5, fill="x")

    def __configuration_group(self):
        self.group3_label = customtkinter.CTkLabel(
            self.right_frame,
            text="Configuration",
            font=customtkinter.CTkFont(size=14, weight="bold"),
        )
        self.group3_label.pack(padx=10, pady=(15, 5))

        self.btn_select_mask = customtkinter.CTkButton(
            self.right_frame, text="Select Mask", command=self.cmd_select_mask
        )
        self.btn_select_mask.pack(padx=20, pady=5, fill="x")

        self.btn_select_calib = customtkinter.CTkButton(
            self.right_frame,
            text="Select Calibration",
            command=self.cmd_select_calibration,
        )
        self.btn_select_calib.pack(padx=20, pady=5, fill="x")

        self.calib_method_var = customtkinter.StringVar(value="linear_regression")
        self.calib_dropdown = customtkinter.CTkOptionMenu(
            self.right_frame,
            values=[
                "linear_regression",
                "linear_interpolation",
                "ransac_regression",
                "huber_regression",
            ],
            variable=self.calib_method_var,
        )
        self.calib_dropdown.pack(padx=20, pady=5, fill="x")

    def __extra_group(self):
        self.group4_label = customtkinter.CTkLabel(
            self.right_frame,
            text="Extra",
            font=customtkinter.CTkFont(size=14, weight="bold"),
        )
        self.group4_label.pack(padx=10, pady=(15, 5))

        self.btn_save_desk = customtkinter.CTkButton(
            self.right_frame, text="Save Desk", command=self.cmd_save_desk
        )
        self.btn_save_desk.pack(padx=20, pady=5, fill="x")

        self.screen_interval_frame = customtkinter.CTkFrame(self.right_frame)
        self.screen_interval_frame.pack(padx=10, pady=5, fill="x")

        self.entry_screen_interval = customtkinter.CTkEntry(
            self.screen_interval_frame, width=60
        )
        self.entry_screen_interval.pack(side="left", padx=5)
        self.entry_screen_interval.insert(0, str(self.screen_update_interval))

        self.btn_set_screen_interval = customtkinter.CTkButton(
            self.screen_interval_frame,
            text="Set Screen Interval",
            command=self.cmd_set_screen_interval,
        )
        self.btn_set_screen_interval.pack(side="left", padx=5, fill="x", expand=True)

        self.desk_interval_frame = customtkinter.CTkFrame(self.right_frame)
        self.desk_interval_frame.pack(padx=10, pady=5, fill="x")

        self.entry_desk_interval = customtkinter.CTkEntry(
            self.desk_interval_frame, width=60
        )
        self.entry_desk_interval.pack(side="left", padx=5)
        self.entry_desk_interval.insert(0, str(self.desk_update_interval))

        self.btn_set_desk_interval = customtkinter.CTkButton(
            self.desk_interval_frame,
            text="Set Desk Interval",
            command=self.cmd_set_desk_interval,
        )
        self.btn_set_desk_interval.pack(side="left", padx=5, fill="x", expand=True)

    def get_inputs(self):
        try:
            return int(self.entry_x.get()), int(self.entry_y.get())
        except ValueError:
            self.status_label.configure(text="Status: Invalid Input")
            return None, None

    def cmd_select_mask(self):
        filepath = filedialog.askopenfilename(
            title="Select a Mask File",
            initialdir=os.path.join(MOTION_MODULE, "resources"),
            filetypes=(("PNG files", "*.png"), ("All files", "*.*")),
        )
        if not filepath:
            return

        try:
            new_mask = Image.open(filepath).convert("RGBA")
            self.motion_module = MotionModule(
                ui_mask=new_mask,
                swipe_calibrator=self.motion_module.swipe_calibrator,
                force_headless=self.motion_module._force_headless,
            )
            self.status_label.configure(text=f"Status: Loaded new mask.")
        except Exception as e:
            self.status_label.configure(text=f"Status: Error loading mask: {e}")

    def cmd_select_calibration(self):
        filepath = filedialog.askopenfilename(
            title="Select a Calibration File",
            initialdir=os.path.join(MOTION_MODULE, "resources"),
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not filepath:
            return

        try:
            method = self.calib_method_var.get()
            calibrator = SwipeCalibrator(filepath, method=method)
            self.motion_module = MotionModule(
                ui_mask=self.motion_module.ui_mask,
                swipe_calibrator=calibrator,
                force_headless=self.motion_module._force_headless,
            )
            self.status_label.configure(text=f"Status: Loaded calibration ({method}).")
        except Exception as e:
            self.status_label.configure(text=f"Status: Error loading calibration: {e}")

    def cmd_save_desk(self):
        desk = self.motion_module.get_desk_copy()
        if desk is not None:
            try:
                filepath = filedialog.asksaveasfilename(
                    title="Save Desk Image",
                    initialdir=os.path.join(MOTION_MODULE, "resources"),
                    defaultextension=".png",
                    filetypes=(("PNG files", "*.png"), ("All files", "*.*")),
                )
                if filepath:
                    Image.fromarray(desk).save(filepath)
                    self.status_label.configure(
                        text=f"Status: Desk saved to {os.path.basename(filepath)}"
                    )
            except Exception as e:
                self.status_label.configure(text=f"Status: Error saving desk: {e}")
        else:
            self.status_label.configure(text="Status: No desk to save")

    def cmd_set_screen_interval(self):
        try:
            val = float(self.entry_screen_interval.get())
            if val > 0:
                self.screen_update_interval = val
                self.status_label.configure(
                    text=f"Status: Screen interval set to {val}s"
                )
            else:
                self.status_label.configure(text="Status: Interval must be > 0")
        except ValueError:
            self.status_label.configure(text="Status: Invalid screen interval")

    def cmd_set_desk_interval(self):
        try:
            val = float(self.entry_desk_interval.get())
            if val > 0:
                self.desk_update_interval = val
                self.status_label.configure(text=f"Status: Desk interval set to {val}s")
            else:
                self.status_label.configure(text="Status: Interval must be > 0")
        except ValueError:
            self.status_label.configure(text="Status: Invalid desk interval")

    def cmd_goto(self):
        x, y = self.get_inputs()
        if x is not None:
            self.status_label.configure(text=f"Status: Executing Goto({x}, {y})")
            threading.Thread(
                target=lambda: self.motion_module.goto((x, y)), daemon=True
            ).start()

    def cmd_goto_action(self):
        x, y = self.get_inputs()
        if x is not None:
            self.status_label.configure(text=f"Status: Executing GotoAction({x}, {y})")
            threading.Thread(
                target=lambda: self.motion_module.goto_for_action((x, y)), daemon=True
            ).start()

    def cmd_move(self):
        dx, dy = self.get_inputs()
        if dx is not None:
            self.status_label.configure(text=f"Status: Executing Move({dx}, {dy})")
            threading.Thread(
                target=lambda: self.motion_module.move_with_offset((dx, dy)),
                daemon=True,
            ).start()

    def cmd_check_position(self):
        self.status_label.configure(text="Status: Checking position...")

        def run():
            try:
                changed = self.motion_module.check_is_position_changed()
                self.after(
                    0,
                    lambda: self.status_label.configure(
                        text=f"Status: Position Changed? {changed}"
                    ),
                )
            except Exception as e:
                self.after(
                    0, lambda: self.status_label.configure(text=f"Status: Error {e}")
                )

        threading.Thread(target=run, daemon=True).start()

    def cmd_set_position(self):
        x, y = self.get_inputs()
        if x is not None:
            self.motion_module.set_current_position((x, y))
            self.status_label.configure(text=f"Status: Set Position to ({x}, {y})")

    def cmd_collapse_desk(self):
        self.motion_module.collapse_desk()
        self.status_label.configure(text="Status: Desk Collapsed")

    def cmd_reset_desk(self):
        self.motion_module.clear_desk()
        self.status_label.configure(text="Status: Desk Cleared")
        self.update_desk()

    def on_desk_press(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.is_panning = False

    def on_desk_drag(self, event):
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        if abs(dx) > 2 or abs(dy) > 2:
            self.is_panning = True
            self.desk_canvas.move("all", dx, dy)
            self.pan_start_x = event.x
            self.pan_start_y = event.y

    def on_desk_release(self, event):
        if not self.is_panning:
            self.process_desk_click(event)
        self.is_panning = False

    def process_desk_click(self, event):
        if self.desk_pil_image is None:
            return

        try:
            coords = self.desk_canvas.coords(self.desk_image_item)
            img_x_offset = coords[0]
            img_y_offset = coords[1]
        except:
            return

        click_x = int(event.x - img_x_offset)
        click_y = int(event.y - img_y_offset)

        w, h = self.desk_pil_image.size

        if click_x < 0 or click_x >= w or click_y < 0 or click_y >= h:
            return

        try:
            pixel = self.desk_pil_image.getpixel((click_x, click_y))
            if len(pixel) == 4 and pixel[3] == 0:
                return
        except Exception as e:
            print(f"Error checking pixel: {e}")
            return

        original_x = click_x * self.desk_scale
        original_y = click_y * self.desk_scale

        print(f"Desk Click: {original_x}, {original_y}")

        desk_x = original_x
        desk_y = original_y

        pos_x, pos_y = self.motion_module.desk_to_position((desk_x, desk_y))
        self.status_label.configure(
            text=f"Desk: ({desk_x}, {desk_y}) | Pos: ({pos_x}, {pos_y})"
        )

        if event.state & 1:
            self.entry_x.delete(0, "end")
            self.entry_x.insert(0, str(pos_x))
            self.entry_y.delete(0, "end")
            self.entry_y.insert(0, str(pos_y))

    def on_screen_click(self, event):
        if not hasattr(self.image_label, "_original_size") or not hasattr(
            self.image_label, "_display_size"
        ):
            return

        widget_w = self.image_label.winfo_width()
        widget_h = self.image_label.winfo_height()

        img_w, img_h = self.image_label._display_size
        orig_w, orig_h = self.image_label._original_size

        pad_x = (widget_w - img_w) // 2
        pad_y = (widget_h - img_h) // 2

        x_on_img = event.x - pad_x
        y_on_img = event.y - pad_y

        if x_on_img < 0 or x_on_img >= img_w or y_on_img < 0 or y_on_img >= img_h:
            return

        scale_x = orig_w / img_w
        scale_y = orig_h / img_h

        screen_x = int(x_on_img * scale_x)
        screen_y = int(y_on_img * scale_y)

        current_pos = self.motion_module.position()
        pos_x = screen_x + current_pos[0]
        pos_y = screen_y + current_pos[1]

        desk_coord = self.motion_module.position_to_desk((pos_x, pos_y))

        print(
            f"Debug Screen Click: widget={widget_w}x{widget_h} img={img_w}x{img_h} event={event.x},{event.y} calc={x_on_img},{y_on_img}"
        )
        self.status_label.configure(
            text=f"Desk: {desk_coord} | Screen: ({screen_x}, {screen_y}) | Pos: ({pos_x}, {pos_y})"
        )

        # Populate inputs on Shift+Click
        if event.state & 1:
            self.entry_x.delete(0, "end")
            self.entry_x.insert(0, str(pos_x))
            self.entry_y.delete(0, "end")
            self.entry_y.insert(0, str(pos_y))

    def update_image(self):
        screenshot = get_screenshot(to_memory=True)
        if screenshot is not None and not isinstance(screenshot, bool):
            try:
                img = Image.fromarray(screenshot).convert("RGBA")
                self.after(0, lambda: self._display_screenshot(img))
            except Exception as e:
                print(f"Error processing image: {e}")

    def _display_screenshot(self, img):
        try:
            target_h = 600
            img_w, img_h = img.size

            ratio = target_h / img_h
            target_w = int(img_w * ratio)

            ctk_image = customtkinter.CTkImage(
                light_image=img, dark_image=img, size=(target_w, target_h)
            )
            self.image_label.configure(image=ctk_image)
            self.image_label._image_ref = ctk_image
            self.image_label._display_size = (target_w, target_h)
            self.image_label._original_size = img.size
        except Exception as e:
            print(f"Error displaying screenshot: {e}")

    def update_desk(self):
        desk = self.motion_module.get_desk_copy()
        if desk is not None:
            try:
                img = Image.fromarray(desk).convert("RGBA")
                self.after(0, lambda: self._display_desk(img))
            except Exception as e:
                print(f"Error processing desk: {e}")

    def _display_desk(self, img):
        try:
            new_width = img.width // self.desk_scale
            new_height = img.height // self.desk_scale
            scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            self.desk_pil_image = scaled_img
            self.desk_tk_image = ImageTk.PhotoImage(scaled_img)

            if self.desk_image_item is None:
                cw = self.desk_canvas.winfo_width()
                ch = self.desk_canvas.winfo_height()

                x = (cw - scaled_img.width) // 2
                y = (ch - scaled_img.height) // 2
                self.desk_image_item = self.desk_canvas.create_image(
                    x, y, image=self.desk_tk_image, anchor="nw"
                )
            else:
                self.desk_canvas.itemconfig(
                    self.desk_image_item, image=self.desk_tk_image
                )
        except Exception as e:
            print(f"Error displaying desk: {e}")

    def update_position_label(self):
        try:
            pos = self.motion_module.position()
            self.position_label.configure(text=f"Position: {pos}")
        except:
            pass

    def live_feed_loop(self):
        while not self.stop_event.is_set():
            self.update_image()
            self.after(0, self.update_position_label)
            time.sleep(self.screen_update_interval)

    def desk_update_loop(self):
        while not self.stop_event.is_set():
            self.update_desk()
            time.sleep(self.desk_update_interval)

    def on_closing(self):
        self.stop_event.set()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
