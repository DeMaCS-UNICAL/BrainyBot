package com.example.tappingbot.model;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.Bitmap;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.NonNull;

import com.android.volley.AuthFailureError;
import com.android.volley.NetworkResponse;
import com.android.volley.Request;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.Volley;
import com.example.tappingbot.controller.HandlerProjection;
import com.example.tappingbot.controller.VolleyMultipartRequest;
import com.example.tappingbot.utils.RWLock;
import com.example.tappingbot.utils.Settings;
import com.koushikdutta.async.http.WebSocket;
import com.koushikdutta.async.http.server.AsyncHttpServer;
import com.koushikdutta.async.http.server.AsyncHttpServerRequest;
import com.koushikdutta.async.http.server.AsyncHttpServerResponse;
import com.koushikdutta.async.http.server.HttpServerRequestCallback;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ImageSender extends Thread {
    private static final String TAG = "ImageSender";
    @SuppressLint("StaticFieldLeak")
    private static ImageSender instance;
    private Context context;
    private RWLock<Boolean> lock;
    private final RWLock<Screenshot> lockImage;
    private static final String REQUEST_IMAGE = "requestimage";

    private ImageSender() {

        lockImage = new RWLock<>();
    }

    public static ImageSender getInstance() {
        if (instance == null)
            instance = new ImageSender();

        return instance;
    }

    public void uploadImage(@NonNull Screenshot screenshot) throws Exception {
        Log.d(TAG, "uploadImage " + screenshot.toString());
        uploadBitmap(screenshot);
    }

    public void setContext(Context context) {
        this.context = context;
    }

    public void setLock(RWLock<Boolean> lock) {
        this.lock = lock;
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
    private byte[] getFileDataFromDrawable(@NonNull Bitmap bitmap) {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.PNG, 80, byteArrayOutputStream);

        bitmap.recycle();
        return byteArrayOutputStream.toByteArray();
    }

    private void uploadBitmap(@NonNull final Screenshot screenshot) throws Exception {

        Log.d(TAG, "insert " + screenshot.toString());
        //our custom volley request
        VolleyMultipartRequest volleyMultipartRequest = new VolleyMultipartRequest(Request.Method.POST, Settings.UPLOAD_URL,
                new Response.Listener<NetworkResponse>() {
                    @Override
                    public void onResponse(NetworkResponse response) {
                        try {
                            JSONObject obj = new JSONObject(new String(response.data));
                            Toast.makeText(context.getApplicationContext(), obj.getString("message"), Toast.LENGTH_SHORT).show();

                        } catch (JSONException e) {
                            e.printStackTrace();
                        }
                    }
                },
                new Response.ErrorListener() {
                    @Override
                    public void onErrorResponse(VolleyError error) {
                        Toast.makeText(context.getApplicationContext(), error.getMessage(), Toast.LENGTH_SHORT).show();
                    }
                }) {

            /*
             * If you want to add more parameters with the image
             * you can do it here
             * here we have only one parameter with the image
             * which is tags
             * */
            @NonNull
            @Override
            protected Map<String, String> getParams() throws AuthFailureError {
                Map<String, String> params = new HashMap<>();
                params.put("tags", "tags");
                return params;
            }

            /*
             * Here we are passing image by renaming it with a unique name
             * */
            @NonNull
            @Override
            protected Map<String, DataPart> getByteData() {
                Map<String, DataPart> params = new HashMap<>();
                params.put("pic", new DataPart(screenshot.getName() + ".png", getFileDataFromDrawable(screenshot.getBitmap())));
                return params;
            }
        };

        //adding the request to volley
        Volley.newRequestQueue(context).add(volleyMultipartRequest);
    }


    @Override
    public void run() {
        Log.e(TAG, "Start Server");

        AsyncHttpServer server = new AsyncHttpServer();

        List<WebSocket> _sockets = new ArrayList<WebSocket>();

        server.get("/", new HttpServerRequestCallback() {
            @Override
            public void onRequest(AsyncHttpServerRequest request, AsyncHttpServerResponse response) {

                if (request.getQuery().toString().contains(REQUEST_IMAGE)) {
                    response.send("ok");
                    try {
                        HandlerProjection.getInstance().startProjection();
                    } catch (Exception e) {
                        e.printStackTrace();
                    }

                } else
                    response.send("not ok");
            }
        });

        server.listen(Settings.localHostServerPort);
    }
}
