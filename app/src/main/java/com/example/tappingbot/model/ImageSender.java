package com.example.tappingbot.model;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.Bitmap;
import android.util.Base64;
import android.util.Log;

import androidx.annotation.NonNull;

import com.example.tappingbot.controller.HandlerProjection;
import com.example.tappingbot.utils.BlockingLock;
import com.example.tappingbot.utils.Settings;
import com.koushikdutta.async.http.server.AsyncHttpServer;
import com.koushikdutta.async.http.server.AsyncHttpServerRequest;
import com.koushikdutta.async.http.server.AsyncHttpServerResponse;
import com.koushikdutta.async.http.server.HttpServerRequestCallback;

import java.io.ByteArrayOutputStream;

public class ImageSender extends Thread {
    private static final String TAG = "ImageSender";
    @SuppressLint("StaticFieldLeak")
    private static ImageSender instance;
    private Context context;
    private final BlockingLock<Screenshot> lockImage;
    private static final String REQUEST_IMAGE = "requestimage";

    private ImageSender() {

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

    public void setContext(Context context) {
        this.context = context;
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
    private String converterBase64(@NonNull Bitmap bitmap) {

        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.PNG, 100, outputStream);

        bitmap.recycle();
        return Base64.encodeToString(outputStream.toByteArray(), Base64.DEFAULT);
    }

    @Override
    public void run() {
        Log.e(TAG, "Start Server");

        AsyncHttpServer server = new AsyncHttpServer();
        server.get("/", new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {

                if (request.getQuery().toString().contains(REQUEST_IMAGE)) {
                    try {
                        response.send("I will send you an image");
                        Log.d(TAG, "onRequest: request");
                        HandlerProjection.getInstance().startProjection();
                        Log.d(TAG, "onRequest: starProjection");

                        Screenshot screenshot = lockImage.take();
                        Log.e(TAG, "take data -> " + screenshot.toString());
                        String base46Image = converterBase64(screenshot.getBitmap());
                        response.send("img/png", base46Image);
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


//        HttpServer server = HttpServer.create(new InetSocketAddress("localhost", 8001), 0);

    }
}
