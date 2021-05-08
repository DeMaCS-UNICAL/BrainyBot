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
import com.example.tappingbot.controller.VolleyMultipartRequest;
import com.example.tappingbot.utils.BlockingQueue;
import com.example.tappingbot.utils.RWLock;
import com.example.tappingbot.utils.Settings;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.util.HashMap;
import java.util.Map;

public class ImageSender extends Thread {
    private static final String TAG = "ImageSender";
    @SuppressLint("StaticFieldLeak")
    private static ImageSender instance;
    private Context context;
    private final BlockingQueue blockingQueue;
    private RWLock<Boolean> lock;

    private ImageSender() {
//        init blockingQueue
        blockingQueue = new BlockingQueue<Screenshot>(Settings.BLOCKING_QUEUE_SIZE);
    }

    public static ImageSender getInstance() {
        if (instance == null)
            instance = new ImageSender();

        return instance;
    }

    public void uploadImage(@NonNull Screenshot screenshot) throws InterruptedException {
        Log.d(TAG, "uploadImage " + screenshot.toString());
        blockingQueue.put(screenshot);
    }

    public void setContext(Context context) {
        this.context = context;
    }

    public void setLock(RWLock<Boolean> lock) {
        this.lock = lock;
    }

    private void insert(@NonNull Screenshot screenshot) {
        //calling the method uploadBitmap to upload image
        Log.d(TAG, "insert " + screenshot.toString());
        uploadBitmap(screenshot);
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

    private void uploadBitmap(final Screenshot screenshot) {


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

        try {
            MessageHandler.connect(Settings.HOST, Settings.PORT);
        } catch (Exception e) {
            e.printStackTrace();
        }

        while (true) {
            try {
                if (!lock.readData()) break;

                Thread.sleep(200);

                Log.d(TAG, "Wait to read message from server");
                if (MessageHandler.read().equals(MessageHandler.TAKE_SCREENSHOT_NOW)) {
                    Object o = blockingQueue.take();
                    if (o instanceof Screenshot) {
                        Screenshot screenshot = (Screenshot) o;
                        insert(screenshot);
                    }
                } else {
                    Log.d(TAG, "Problem MessageHandler.read()");
                }

            } catch (Exception e) {
                e.printStackTrace();
                break;
            }
        }
    }
}
