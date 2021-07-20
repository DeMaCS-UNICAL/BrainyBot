package com.application.tappingbot;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;

import androidx.appcompat.app.AppCompatActivity;

import com.application.tappingbot.model.ImageSender;
import com.application.tappingbot.model.ScreenCaptureService;
import com.application.tappingbot.utils.Settings;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    private Button startStop;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        startStop = findViewById(R.id.start_stop);
        final boolean[] isStarted = {false};

        startStop.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    if (isStarted[0])
                        stop();
                    else
                        start();

                    isStarted[0] = !isStarted[0];
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });


    }

    private void start() throws Exception {
        Log.d(TAG, "start: ");
        //        change label text
        startStop.setText(R.string.stop);


        // start projection
        startProjection();
        // start server
        ImageSender.getInstance().startServer();

    }

    @SuppressLint("SetTextI18n")
    private void stop() throws Exception {
        Log.d(TAG, "stop: ");
//        change label text
        startStop.setText(R.string.start);

//        stop projection
        stopProjection();

//        stop server
        ImageSender.getInstance().stopServer();
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


    private void stopProjection() {
        Log.d(TAG, "stopProjection: ");
        MainActivity.this.startService(ScreenCaptureService.getStopIntent(MainActivity.this));
    }

    private void startProjection() {

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