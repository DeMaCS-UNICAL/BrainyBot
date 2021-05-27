package com.example.tappingbot;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Bundle;
import android.util.Log;

import androidx.appcompat.app.AppCompatActivity;

import com.example.tappingbot.controller.HandlerProjection;
import com.example.tappingbot.model.ImageSender;
import com.example.tappingbot.model.ScreenCaptureService;
import com.example.tappingbot.utils.Settings;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    private final boolean isStart = true;
    private ExecutorService pool;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        //        init HandlerProjection
        HandlerProjection.setActivity(this);

        startProjection();

        //        init thread image sender
        pool = Executors.newFixedThreadPool(Settings.POOL_SIZE);
        pool.execute(ImageSender.getInstance());


    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) { // result of startActivityForResult
        Log.d(TAG, "onActivityResult");
        if (requestCode == Settings.REQUEST_CODE) {
            if (resultCode == Activity.RESULT_OK) {
                startService(ScreenCaptureService.getStartIntent(this, resultCode, data)); // start capture
            }
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    /****************************************** UI Widget Callbacks *******************************/


    public void stopProjection() {
        Log.d(TAG, "stopProjection: ");
        MainActivity.this.startService(ScreenCaptureService.getStopIntent(MainActivity.this));
    }

    public void startProjection() {

        Log.d(TAG, "startProjection: first");
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
                (MediaProjectionManager) MainActivity.this.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        MainActivity.this.startActivityForResult(mProjectionManager.createScreenCaptureIntent(), Settings.REQUEST_CODE);
        Log.d(TAG, "startProjection: startActivityForResult");
    }
}