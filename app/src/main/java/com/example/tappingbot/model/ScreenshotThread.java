package com.example.tappingbot.model;

import android.graphics.Bitmap;
import android.util.Log;
import android.view.View;

import java.io.File;

import github.nisrulz.screenshott.ScreenShott;

public class ScreenshotThread extends Thread {
    private static final String TAG = ScreenshotThread.class.getCanonicalName();
    private final View view;
    private int idFile;

    public ScreenshotThread(View view) {
        this.view = view;
        this.idFile = 0;
    }

    private Bitmap takeScreen() throws Exception {
        // View with spaces as per constraints
        Bitmap bitmapView = ScreenShott.getInstance().takeScreenShotOfView(view);
        Log.d(TAG, "takeScreen: " + bitmapView); //debug
        return bitmapView;
    }

    private void saveScreen(Bitmap bitmapView) throws Exception {
        // save file
        File file = ScreenShott.getInstance().saveScreenshotToPicturesFolder(view.getContext(), bitmapView, "Screen N." + idFile++ + " In Date -> ");
        Log.d(TAG, "saveScreen: " + file); //debug
    }

    @Override
    public void run() { //take screen each second
        super.run();
        while (true) {
            try {

                Bitmap bitmapView = takeScreen();
                saveScreen(bitmapView);

                sleep(1000);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
