package com.application.screenshotserver.model;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Display;
import android.view.WindowManager;

import androidx.annotation.NonNull;

import org.jetbrains.annotations.Contract;

import java.nio.ByteBuffer;

public class HandlerScreenshot {
    private static final String TAG = "HandlerScreenshot";
    private static final String SCREENCAP_NAME = "Mario Avolio Capture";
    private static final Builder builderInstance;
    private static HandlerScreenshot instance;

    static {
        builderInstance = new Builder();
    }

    private WindowManager windowManager;
    private Integer resultCode;
    private Intent data;
    private int mDensity;
    private int mWidth;
    private int mHeight;
    private MediaProjectionManager mpManager;
    private MediaProjection mMediaProjection;
    private Handler mHandler;
    private ImageReader mImageReader;

    public HandlerScreenshot(WindowManager windowManager, MediaProjectionManager mpManager, Integer resultCode, Intent data) {
        this.windowManager = windowManager;
        this.mpManager = mpManager;
        this.resultCode = resultCode;
        this.data = data;
        startLooper();
    }

    private HandlerScreenshot() {
        startLooper();
    }

    public static Builder getBuilder() {
        return builderInstance;
    }

    public static HandlerScreenshot getInstance() throws Exception {

        if (!builderInstance.isComplete())
            throw new Exception("Not Built.");


        if (instance == null)
            instance = builderInstance.build();
        return instance;
    }

    private static int getVirtualDisplayFlags() {
        Log.d(TAG, "getVirtualDisplayFlags");
        return DisplayManager.VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY | DisplayManager.VIRTUAL_DISPLAY_FLAG_PUBLIC;
    }

    public void takeScreenshot() {
        Log.d(TAG, "startProjection");

        if (mMediaProjection == null) {
            Log.d(TAG, "takeScreenshot: ");
            mMediaProjection = mpManager.getMediaProjection(resultCode, data);
            if (mMediaProjection != null) {
                // display metrics
                mDensity = Resources.getSystem().getDisplayMetrics().densityDpi;
                Display mDisplay = windowManager.getDefaultDisplay();

                // create virtual display depending on device width / height
                createVirtualDisplay(); // initialize virtual display

            }
        }
    }

    @SuppressLint("WrongConstant")
    private void createVirtualDisplay() {
        Log.d(TAG, "createVirtualDisplay");

        // get width and height
        mWidth = Resources.getSystem().getDisplayMetrics().widthPixels;
        mHeight = Resources.getSystem().getDisplayMetrics().heightPixels;

        // start capture reader
        mImageReader = ImageReader.newInstance(mWidth, mHeight, PixelFormat.RGBA_8888, 2); // contains the surface on we render

        // initialize our virtual display
        mMediaProjection.createVirtualDisplay(SCREENCAP_NAME, mWidth, mHeight,
                mDensity, getVirtualDisplayFlags(), mImageReader.getSurface(), null, mHandler);

        mImageReader.setOnImageAvailableListener(new ImageAvailableListener(), mHandler);
    }

    private void startLooper() {
        new Thread() {
            @Override
            public void run() {
                try {
                    Looper.prepare();


                    Log.d(TAG, "I am between two looper.I am waiting to take screenshot...");

                    /*
                     *   A Handler allows you to send and process Message and Runnable objects associated with a thread's MessageQueue.
                     *   Each Handler instance is associated with a single thread and that thread's message queue.
                     *   When you create a new Handler it is bound to a Looper.
                     *   It will deliver messages and runnables to that Looper's message queue and execute them on that Looper's thread.
                     *
                     * */
                    mHandler = new Handler();

                    /*
                     * Loop is a Class used to run a message loop for a thread.
                     * Threads by default do not have a message loop associated with them; to create one, call prepare()
                     * in the thread that is to run the loop, and then loop() to have it process messages until the loop is stopped.
                     * */
                    Looper.loop();

                } catch (Exception e) {

                    Log.e(TAG, "ERROR IN LOOPER");
                    e.printStackTrace();
                }

            }
        }.start();
    }

    public static class Builder {

        private WindowManager windowManager;
        private MediaProjectionManager mpManager;
        private Integer resultCode;
        private Intent data;

        public Builder setWindowManager(WindowManager windowManager) {
            Log.d(TAG, "setWindowManager: ");
            this.windowManager = windowManager;
            return builderInstance;
        }

        public Builder setMpManager(MediaProjectionManager mpManager) {
            Log.d(TAG, "setMpManager: ");
            this.mpManager = mpManager;
            return builderInstance;
        }

        public Builder setResultCode(int resultCode) {
            Log.d(TAG, "setResultCode: ");
            this.resultCode = resultCode;
            return builderInstance;
        }

        public Builder setIntent(Intent data) {
            Log.d(TAG, "setIntent: ");
            this.data = data;
            return builderInstance;
        }

        @NonNull
        @Contract(value = " -> new", pure = true)
        private HandlerScreenshot build() {
            return new HandlerScreenshot(windowManager, mpManager, resultCode, data);
        }

        private boolean isComplete() {
            return this.data != null && this.windowManager != null && this.resultCode != null && this.mpManager != null;
        }
    }

    private class ImageAvailableListener implements ImageReader.OnImageAvailableListener { // management by an handler

        @Override
        public void onImageAvailable(ImageReader reader) {

            Log.d(TAG, "onImageAvailable");

//            it can make only one screenshot
            mHandler.post(new Runnable() {
                @Override
                public void run() {
                    mImageReader.setOnImageAvailableListener(null, mHandler);
                    mMediaProjection.stop();
                    mMediaProjection = null;
                    mImageReader = null;
                }
            });

            try (Image image = mImageReader.acquireLatestImage()) { // acquire last image
                if (image != null) {
                    Image.Plane[] planes = image.getPlanes();
                    ByteBuffer buffer = planes[0].getBuffer();
                    int pixelStride = planes[0].getPixelStride();
                    int rowStride = planes[0].getRowStride();
                    int rowPadding = rowStride - pixelStride * mWidth;

                    // create bitmap
                    Bitmap bitmap = Bitmap.createBitmap(mWidth + rowPadding / pixelStride, mHeight, Bitmap.Config.ARGB_8888);
                    bitmap.copyPixelsFromBuffer(buffer);

                    ImageSender.getInstance().uploadImage(bitmap);
                    Log.e(TAG, "screenshot name: " + bitmap);

                }

            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
