package com.example.tappingbot;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import com.example.tappingbot.model.ScreenshotThread;
import com.example.tappingbot.model.StopScreenshot;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = MainActivity.class.getCanonicalName();
    private Button startAndStopButton;
    private ExecutorService pool;
    private StopScreenshot stopScreenshot;
    private boolean isStart = true;

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
                    Thread t = new ScreenshotThread(MainActivity.this.findViewById(android.R.id.content), stopScreenshot);

                    try {

                        if (isStart) {
                            stopScreenshot.stopWithLock(false);

                            pool.execute(t);
                            startAndStopButton.setText(R.string.stop);
                        } else {
                            stopScreenshot.stopWithLock(true);
                            startAndStopButton.setText(R.string.start);
                        }

                    } catch (InterruptedException e) {
                        e.printStackTrace();
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
}