package com.application.ScreenshotServer.model;

import android.app.Activity;
import android.app.Notification;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.IBinder;
import android.util.Log;
import android.view.WindowManager;

import androidx.annotation.NonNull;
import androidx.core.util.Pair;

import com.application.ScreenshotServer.utils.NotificationUtils;

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
    private HandlerScreenshot.Builder builder;


    @Override
    public void onCreate() {
        Log.d(TAG, "onCreate");
        super.onCreate();// start capture handling thread
        builder = HandlerScreenshot.getBuilder();


//        MediaProjectionManager is the class to start capturing the screen.
        MediaProjectionManager mpManager =
                (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);

        WindowManager windowManager = (WindowManager) getSystemService(Context.WINDOW_SERVICE);

//        building Screenshot tool
        builder.setWindowManager(windowManager).setMpManager(mpManager);

    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "onStartCommand");

        try {
            if (isStartCommand(intent)) {
                // create notification
                Pair<Integer, Notification> notification = NotificationUtils.getNotification(this);
                startForeground(notification.first, notification.second);
                // start projection
                int resultCode = intent.getIntExtra(RESULT_CODE, Activity.RESULT_CANCELED);
                Intent data = intent.getParcelableExtra(DATA);
                builder.setResultCode(resultCode).setIntent(data);

            } else if (isStopCommand(intent)) {
                stopSelf();
            } else {
                stopSelf();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        return START_NOT_STICKY;
    }


    @Override
    public IBinder onBind(Intent intent) {
        Log.d(TAG, "onBind");
        return null;
    }

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

    private boolean isStartCommand(@NonNull Intent intent) {
        Log.d(TAG, "isStartCommand");

        return intent.hasExtra(RESULT_CODE) && intent.hasExtra(DATA)
                && intent.hasExtra(ACTION) && Objects.equals(intent.getStringExtra(ACTION), START);
    }

    private boolean isStopCommand(@NonNull Intent intent) {
        Log.d(TAG, "isStopCommand");

        return intent.hasExtra(ACTION) && Objects.equals(intent.getStringExtra(ACTION), STOP);
    }

}