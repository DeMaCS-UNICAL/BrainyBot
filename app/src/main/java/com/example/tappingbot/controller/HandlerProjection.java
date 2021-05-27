package com.example.tappingbot.controller;

import android.annotation.SuppressLint;
import android.app.Activity;

public class HandlerProjection {
    private static final String TAG = "HandlerProjection";
    @SuppressLint("StaticFieldLeak")
    private static HandlerProjection instance;
    @SuppressLint("StaticFieldLeak")
    private static Activity activity;


    private HandlerProjection() {
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
}
