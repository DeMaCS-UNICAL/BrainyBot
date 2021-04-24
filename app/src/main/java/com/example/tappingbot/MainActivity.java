package com.example.tappingbot;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.projection.MediaProjectionManager;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import com.example.tappingbot.model.ScreenCaptureService;
import com.example.tappingbot.model.StopScreenshot;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = MainActivity.class.getCanonicalName();
    private Button startAndStopButton;
    private ExecutorService pool;
    private StopScreenshot stopScreenshot;
    private boolean isStart = true;
    private static final int REQUEST_CODE = 100;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // stop variable
        stopScreenshot = new StopScreenshot();

        // initialize threads pool
        final int poolSize = 1;
        pool = Executors.newFixedThreadPool(poolSize);

        // button start and stop
        Button startAndStopButton = findViewById(R.id.start_button);
        startAndStopButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                if (isStoragePermissionGranted()) {

                    // Thread to take screenshot
//                    Thread t = new ScreenshotThread(MainActivity.this.findViewById(android.R.id.content), stopScreenshot);


                    if (isStart) {
//                            stopScreenshot.stopWithLock(false);
                        startProjection();
//                            pool.execute(t);
                        startAndStopButton.setText(R.string.stop);
                    } else {
//                            stopScreenshot.stopWithLock(true);
                        stopProjection();
                        startAndStopButton.setText(R.string.start);
                    }


                    isStart = !isStart;
                }
            }
        });
    }

    private boolean isStoragePermissionGranted() {
        if (checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                == PackageManager.PERMISSION_GRANTED) {
            Log.v(TAG, "Permission is granted");
            return true;
        } else {

            Log.v(TAG, "Permission is revoked");
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, 1);
            return false;
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            Log.v(TAG, "Permission: " + permissions[0] + "was " + grantResults[0]);
            //resume tasks needing this permission
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQUEST_CODE) {
            if (resultCode == Activity.RESULT_OK) {
                startService(ScreenCaptureService.getStartIntent(this, resultCode, data));
            }
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    /****************************************** UI Widget Callbacks *******************************/
    private void startProjection() {
        MediaProjectionManager mProjectionManager =
                (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        startActivityForResult(mProjectionManager.createScreenCaptureIntent(), REQUEST_CODE);
    }

    private void stopProjection() {
        startService(ScreenCaptureService.getStopIntent(this));
    }
}