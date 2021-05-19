package com.example.tappingbot;

import android.app.Activity;
import android.content.Intent;
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

//        init thread image sender
        pool = Executors.newFixedThreadPool(Settings.POOL_SIZE);
        ImageSender.getInstance().setContext(MainActivity.this);
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
}