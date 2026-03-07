import os
import tempfile
import subprocess
import threading
import time
import cv2
import av
# Require PyAv

class ScrcpyStream:
    def __init__(self):
        self.latest_frame = None
        self.running = True
        
        self.fifo_path = os.path.join(tempfile.gettempdir(), "scrcpy_video.mkv")
        
        if os.path.exists(self.fifo_path):
            os.remove(self.fifo_path)
        os.mkfifo(self.fifo_path)
        
        print("Starting headless Scrcpy process (v3.x compatible)...")
        
        self.process = subprocess.Popen(
            [
                "scrcpy",
                "--no-playback",
                "--no-audio",
                "--max-fps=15",
                "--record-format=mkv",
                f"--record={self.fifo_path}"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        
        time.sleep(2)
    
    def _stream_loop(self):
        try:
            container = av.open(self.fifo_path)
            stream = container.streams.video[0]
            
            for frame in container.decode(stream):
                if not self.running:
                    break
                self.latest_frame = frame.to_ndarray(format='bgr24')
        
        except Exception as e:
            if self.running:
                print(f"\n[Stream Error] Connection lost or failed: {e}")
    
    def get_frame(self):
        return self.latest_frame
    
    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        if os.path.exists(self.fifo_path):
            os.remove(self.fifo_path)
        
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=2)


def main():
    stream = ScrcpyStream()
    
    if stream.process.poll() is not None:
        print("Error: scrcpy failed to start. Is the device connected?")
        return
    
    print("Scrcpy stream connected and decoding in background!")
    
    try:
        while True:
            cmd = input("\nPress [ENTER] to capture a frame (or type 'q' to quit): ")
            
            if cmd.lower() == 'q':
                break
            
            frame = stream.get_frame()
            
            if frame is not None:
                print("Frame captured! Focus the image window and press any key to close it.")

                # height, width = frame.shape[:2]
                # if height > 1080:
                #     scale = 1080 / height
                #     frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
                #
                cv2.imshow("Captured Frame", frame)
                cv2.waitKey(0)
                cv2.destroyWindow("Captured Frame")
            else:
                print("Stream is still buffering or device is off, try again in a second.")
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("Shutting down scrcpy stream...")
        stream.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()