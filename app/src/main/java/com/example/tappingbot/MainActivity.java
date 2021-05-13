package com.example.tappingbot;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;

import com.example.tappingbot.controller.HandlerProjection;
import com.example.tappingbot.model.ImageSender;
import com.example.tappingbot.model.ScreenCaptureService;
import com.example.tappingbot.utils.RWLock;
import com.example.tappingbot.utils.Settings;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = MainActivity.class.getCanonicalName();
    private final boolean isStart = true;
    private ExecutorService pool;
    private RWLock<Boolean> rwLock;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

//        init HandlerProjection
        HandlerProjection.setActivity(MainActivity.this);

//        init thread image sender
        pool = Executors.newFixedThreadPool(Settings.POOL_SIZE);
        ImageSender.getInstance().setContext(MainActivity.this);
        ImageSender.getInstance().setLock(rwLock);
        pool.execute(ImageSender.getInstance());

    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) { // result of startActivityForResult
        if (requestCode == Settings.REQUEST_CODE) {
            if (resultCode == Activity.RESULT_OK) {
                startService(ScreenCaptureService.getStartIntent(this, resultCode, data)); // start capture
            }
        }
        super.onActivityResult(requestCode, resultCode, data);
    }
}