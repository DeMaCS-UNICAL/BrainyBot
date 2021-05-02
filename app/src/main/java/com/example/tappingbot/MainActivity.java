package com.example.tappingbot;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;

import androidx.appcompat.app.AppCompatActivity;

import com.example.tappingbot.model.ImageSender;
import com.example.tappingbot.model.ScreenCaptureService;
import com.example.tappingbot.utils.RWLock;
import com.example.tappingbot.utils.Settings;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = MainActivity.class.getCanonicalName();
    private boolean isStart = true;
    private ExecutorService pool;
    private RWLock<Boolean> rwLock;
    private boolean stop;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

//        init Read Write Lock
        stop = false;
        rwLock = new RWLock<Boolean>(stop);

//        init thread image sender
        pool = Executors.newFixedThreadPool(Settings.POOL_SIZE);
        ImageSender.getInstance().setContext(MainActivity.this);
        ImageSender.getInstance().setLock(rwLock);

        // button start and stop
        Button startAndStopButton = findViewById(R.id.start_button);
        startAndStopButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
//                if (isStoragePermissionGranted()) {
                if (isStart) {

                    try {
                        rwLock.writeData(true);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }

                    pool.execute(ImageSender.getInstance());
                    startProjection();
                    startAndStopButton.setText(R.string.stop);
                } else {

                    try {
                        rwLock.takeWriteLock();
                        rwLock.setData(false);
                        stopProjection();
                        startAndStopButton.setText(R.string.start);

                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    } finally {
                        rwLock.leaveWriteLock();
                    }
                }
                isStart = !isStart;
//                }
            }
        });
    }

//    private boolean isStoragePermissionGranted() {
//        if (checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE)
//                == PackageManager.PERMISSION_GRANTED) {
//            Log.v(TAG, "Permission is granted");
//            return true;
//        } else {
//
//            Log.v(TAG, "Permission is revoked");
//            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, 1);
//            return false;
//        }
//    }
//
//    @Override
//    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
//        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
//        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
//            Log.v(TAG, "Permission: " + permissions[0] + "was " + grantResults[0]);
//            //resume tasks needing this permission
//        }
//    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) { // result of startActivityForResult
        if (requestCode == Settings.REQUEST_CODE) {
            if (resultCode == Activity.RESULT_OK) {
                startService(ScreenCaptureService.getStartIntent(this, resultCode, data)); // start capture
            }
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    /****************************************** UI Widget Callbacks *******************************/
    private void startProjection() {

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
                (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        startActivityForResult(mProjectionManager.createScreenCaptureIntent(), Settings.REQUEST_CODE);
    }

    private void stopProjection() {
        startService(ScreenCaptureService.getStopIntent(this));
    }
}