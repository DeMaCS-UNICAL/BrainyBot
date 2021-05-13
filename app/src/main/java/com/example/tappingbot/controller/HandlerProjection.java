package com.example.tappingbot.controller;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.media.projection.MediaProjectionManager;

import com.example.tappingbot.model.ScreenCaptureService;
import com.example.tappingbot.utils.Settings;

public class HandlerProjection {
    @SuppressLint("StaticFieldLeak")
    private static HandlerProjection instance;
    @SuppressLint("StaticFieldLeak")
    private static Activity activity;
    private boolean isStarted;

    private HandlerProjection() {
        isStarted = false;
    }

    public static HandlerProjection getInstance() throws Exception {
        if (activity == null)
            throw new Exception("activity == null");

        if (instance == null)
            instance = new HandlerProjection();
        return instance;
    }

    public static void setActivity(Activity activity) {
        HandlerProjection.activity = activity;
    }

    /****************************************** UI Widget Callbacks *******************************/
    public void startProjection() {
        if (isStarted)
            isStarted = false;


        /*
         *   - MediaProjection has a particular class: MediaProjectionManager
         *   - MediaProjectionManager serves to capture screenshot but NOT to capture audio of device.
         *   - MediaProjectionManager has 2 functions:
         *       + createScreenCaptureIntent() -> can be passed at startActivityForResult to start capturing the screen.
         *                                     -> The result of activity will be passed to getMediaProjection()
         *
         *       + getMediaProjection() -> Take as input an Intent ( results of createScreenCaptureIntent() )
         *                               -> returns MediaProjection
         * */

        MediaProjectionManager mProjectionManager =
                (MediaProjectionManager) activity.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        activity.startActivityForResult(mProjectionManager.createScreenCaptureIntent(), Settings.REQUEST_CODE);
    }

    public void stopProjection() {
        activity.startService(ScreenCaptureService.getStopIntent(activity));
    }

    public boolean isStarted() {
        return isStarted;
    }

    public void setStarted(boolean started) {
        isStarted = started;
    }
}
