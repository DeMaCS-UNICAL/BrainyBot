package com.application.ScreenshotServer.model;

import android.annotation.SuppressLint;
import android.graphics.Bitmap;
import android.util.Log;

import androidx.annotation.NonNull;

import com.application.ScreenshotServer.utils.BlockingLock;
import com.application.ScreenshotServer.utils.Settings;
import com.koushikdutta.async.http.server.AsyncHttpServer;
import com.koushikdutta.async.http.server.AsyncHttpServerRequest;
import com.koushikdutta.async.http.server.AsyncHttpServerResponse;
import com.koushikdutta.async.http.server.HttpServerRequestCallback;

import java.io.ByteArrayOutputStream;

public class ImageSender {
    private static final String TAG = "ImageSender";
    @SuppressLint("StaticFieldLeak")
    private static ImageSender instance;
    private final BlockingLock<Screenshot> lockImage;
    private static final String REQUEST_IMAGE = "requestimage";
    private final AsyncHttpServer server;

    private ImageSender() {

        server = new AsyncHttpServer();
        lockImage = new BlockingLock<>();
    }

    public static ImageSender getInstance() {
        if (instance == null)
            instance = new ImageSender();

        return instance;
    }

    public void uploadImage(@NonNull Screenshot screenshot) throws Exception {
        lockImage.put(screenshot);
        Log.d(TAG, "uploadImage " + screenshot.toString());
    }

    /*
     * The method is taking Bitmap as an argument
     * then it will return the byte[] array for the given bitmap
     * and we will send this array to the server
     * here we are using PNG Compression with 80% quality
     * you can give quality between 0 to 100
     * 0 means worse quality
     * 100 means best quality
     * */
    @NonNull
    private byte[] convertToArray(@NonNull Bitmap bitmap) {

        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.PNG, 100, outputStream);

        bitmap.recycle();
        return outputStream.toByteArray();
    }

    public void startServer() throws Exception {
        Log.e(TAG, "Start Server");
        server.get("/", new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {

                if (request.getQuery().toString().contains(REQUEST_IMAGE)) {
                    try {
                        Log.d(TAG, "onRequest: request");
                        HandlerScreenshot.getInstance().takeScreenshot();
                        Screenshot screenshot = lockImage.take();
                        Log.e(TAG, "take data -> " + screenshot.toString());
                        byte[] bytes = convertToArray(screenshot.getBitmap());
                        response.send("image/png", bytes);
                        Log.e(TAG, "send data");
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                } else {
                    Log.d(TAG, "onRequest: Error");
                    response.send("ERROR");
                }
            }
        });

        Log.e(TAG, "listening in " + Settings.PORT);

        server.listen(Settings.PORT);
    }

    public void stopServer() throws Exception {
        server.stop();
    }
}
