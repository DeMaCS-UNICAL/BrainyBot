#!/bin/bash

echo "🎥 Starting scrcpy recording for 3 seconds..."
scrcpy --video-codec=h265 --video-encoder=c2.qti.hevc.encoder --record=output_h265.mkv --video-bit-rate=100M --no-audio --time-limit=3 &

sleep 1.5

echo "📸 Capturing ground truth..."
adb exec-out screencap -p > ground_truth.png

echo "⏳ Waiting for scrcpy to finalize the video..."
wait

echo "🎞️ Extracting video frame..."
# -ss 00:00:01.500 seeks to the 1.5-second mark to match our screencap timing
ffmpeg -y -ss 00:00:01.500 -i output_h265.mkv -frames:v 1 h265_frame.png -loglevel warning

echo "🗑️ Cleaning up video file..."
rm output_h265.mkv

echo "🔍 Generating difference map..."
compare ground_truth.png h265_frame.png difference_map.png

echo "✅ Done! Check difference_map.png."
