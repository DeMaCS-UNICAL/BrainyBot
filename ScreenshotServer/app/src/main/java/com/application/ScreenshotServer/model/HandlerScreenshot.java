package com.application.ScreenshotServer.model;

public class HandlerScreenshot {
    private static HandlerScreenshot instance;

    public static HandlerScreenshot getInstance() {
        return instance;
    }

    private HandlerScreenshot() {
    }
}
