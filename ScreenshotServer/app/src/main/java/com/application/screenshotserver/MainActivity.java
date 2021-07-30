package com.application.screenshotserver;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;

import androidx.appcompat.app.AppCompatActivity;

import com.application.screenshotserver.model.ImageSender;
import com.application.screenshotserver.model.ScreenCaptureService;
import com.application.screenshotserver.utils.Settings;

import java.util.HashMap;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    private Button startStop;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        startStop = findViewById(R.id.start_stop);

        ContextState contextState = new ContextState(ContextState.STOP);
        startStop.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    contextState.changeState();
                    contextState.getState().execute();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });

    }

    private interface State {
        void execute() throws Exception;
    }


    private class ContextState {
        public static final String START = "START";
        public static final String STOP = "STOP";

        private State state;
        private final HashMap<String, State> stringStateHashMap;

        public ContextState(String state) {

            stringStateHashMap = new HashMap<>();

            try {
                setState(state);
            } catch (Exception e) {
                try {
                    setState(STOP);
                } catch (Exception exception) {
                    exception.printStackTrace();
                }
            }
        }

        public void changeState() throws Exception {
            if (this.state instanceof Start)
                setState(STOP);
            else
                setState(START);
        }

        private void setState(String state) throws Exception {

            State stateTmp = null;
            if (stringStateHashMap.containsKey(state))
                stateTmp = stringStateHashMap.get(state);
            else {
                switch (state) {
                    case START:
                        stateTmp = new Start();
                        break;
                    case STOP:
                        stateTmp = new Stop();
                        break;
                    default:
                        throw new Exception("State does not exist.");
                }

                stringStateHashMap.put(state, stateTmp);
            }

            Log.d(TAG, "setState: " + state);
            this.state = stateTmp;
        }

        public State getState() {
            return state;
        }
    }

    private class Start implements State {

        @Override
        public void execute() throws Exception {

            Log.d(TAG, "start: ");
            //  change label text
            startStop.setText(R.string.stop);
            // start projection
            startProjection();
            // start server
            ImageSender.getInstance().startServer();

        }
    }

    private class Stop implements State {

        @Override
        public void execute() throws Exception {
            Log.d(TAG, "stop: ");
            //  change label text
            startStop.setText(R.string.start);
            //  stop projection
            stopProjection();
            //  stop server
            ImageSender.getInstance().stopServer();
        }
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