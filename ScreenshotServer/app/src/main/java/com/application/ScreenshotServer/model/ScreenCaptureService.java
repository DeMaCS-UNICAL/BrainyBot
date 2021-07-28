package com.application.ScreenshotServer.model;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.Notification;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;
import android.view.Display;
import android.view.WindowManager;

import androidx.annotation.NonNull;
import androidx.core.util.Pair;

import com.application.ScreenshotServer.utils.NotificationUtils;

import java.nio.ByteBuffer;
import java.util.Objects;

public class ScreenCaptureService extends Service {


    /*
     *   CALL ORDER LIST:
     *       - getStartIntent
     *       - onCreate
     *       - onStartCommand
     *       - startProjection
     *          - createVirtualDisplay
     *          - getVirtualDisplayFlags
     *          - onImageAvailable (loop)
     *       - getStopIntent
     * */

    private static final String TAG = "ScreenCaptureService";
    private static final String RESULT_CODE = "RESULT_CODE";
    private static final String DATA = "DATA";
    private static final String ACTION = "ACTION";
    private static final String START = "START";
    private static final String STOP = "STOP";
    private static final String SCREENCAP_NAME = "TappingBOT Capture Service";
    private MediaProjection mMediaProjection;
    private ImageReader mImageReader;
    private Handler mHandler;
    private int mDensity;
    private int mWidth;
    private int mHeight;
    private int resultCode;
    private Intent data;

    private void startProjection(int resultCode, Intent data) {
        Log.d(TAG, "startProjection");

        this.resultCode = resultCode;
        this.data = data;


        /*
         *
         *   MediaProjectionManager is the class to start capturing the screen.
         *   at line 125 we take MediaProjection.
         *
         * */
        MediaProjectionManager mpManager =
                (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);


        if (mMediaProjection == null) {
            mMediaProjection = mpManager.getMediaProjection(resultCode, data);
            if (mMediaProjection != null) {
                // display metrics
                mDensity = Resources.getSystem().getDisplayMetrics().densityDpi;
                WindowManager windowManager = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
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

        VirtualDisplay mVirtualDisplay = mMediaProjection.createVirtualDisplay(SCREENCAP_NAME, mWidth, mHeight,
                mDensity, getVirtualDisplayFlags(), mImageReader.getSurface(), null, mHandler);

        mImageReader.setOnImageAvailableListener(new ImageAvailableListener(), mHandler);
    }

    @Override
    public void onCreate() {
        Log.d(TAG, "onCreate");
        super.onCreate();// start capture handling thread
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

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "onStartCommand");

        if (isStartCommand(intent)) {
            // create notification
            Pair<Integer, Notification> notification = NotificationUtils.getNotification(this);
            startForeground(notification.first, notification.second);
            // start projection
            int resultCode = intent.getIntExtra(RESULT_CODE, Activity.RESULT_CANCELED);
            Intent data = intent.getParcelableExtra(DATA);
            startProjection(resultCode, data);
        } else if (isStopCommand(intent)) {
            stopProjection();
            stopSelf();
        } else {
            stopSelf();
        }

        return START_NOT_STICKY;
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

                    Screenshot screenshot = new Screenshot(bitmap, Integer.toString(0));
                    ImageSender.getInstance().uploadImage(screenshot);
                    Log.e(TAG, "screenshot name: " + screenshot);

                }

            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }


    private void stopProjection() {
        Log.d(TAG, "stopProjection");

        if (mHandler != null) {
            mHandler.post(new Runnable() {
                @Override
                public void run() {
                    if (mMediaProjection != null) {
                        mMediaProjection.stop();
                    }
                }
            });
        }
    }

    private static boolean isStartCommand(@NonNull Intent intent) {
        Log.d(TAG, "isStartCommand");

        return intent.hasExtra(RESULT_CODE) && intent.hasExtra(DATA)
                && intent.hasExtra(ACTION) && Objects.equals(intent.getStringExtra(ACTION), START);
    }

    private static boolean isStopCommand(@NonNull Intent intent) {
        Log.d(TAG, "isStopCommand");

        return intent.hasExtra(ACTION) && Objects.equals(intent.getStringExtra(ACTION), STOP);
    }

    private static int getVirtualDisplayFlags() {
        Log.d(TAG, "getVirtualDisplayFlags");
        return DisplayManager.VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY | DisplayManager.VIRTUAL_DISPLAY_FLAG_PUBLIC;
    }

    @Override
    public IBinder onBind(Intent intent) {
        Log.d(TAG, "onBind");
        return null;
    }

    //    first call
    @NonNull
    public static Intent getStartIntent(Context context, int resultCode, Intent data) {
        Log.d(TAG, "getStartIntent");

        Intent intent = new Intent(context, ScreenCaptureService.class);
        intent.putExtra(ACTION, START);
        intent.putExtra(RESULT_CODE, resultCode);
        intent.putExtra(DATA, data);
        return intent;
    }

    @NonNull
    public static Intent getStopIntent(Context context) {
        Log.d(TAG, "getStopIntent");
        Intent intent = new Intent(context, ScreenCaptureService.class);
        intent.putExtra(ACTION, STOP);
        return intent;
    }
}