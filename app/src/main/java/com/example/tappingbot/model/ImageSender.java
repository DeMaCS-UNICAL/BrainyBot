package com.example.tappingbot.model;

import android.content.Context;
import android.graphics.Bitmap;
import android.util.Base64;
import android.util.Log;

import com.example.tappingbot.utils.BlockingQueue;
import com.example.tappingbot.utils.RWLock;
import com.example.tappingbot.utils.Settings;

import java.io.ByteArrayOutputStream;

public class ImageSender extends Thread {
    private static final String TAG = "ImageSender";
    private static ImageSender instance;
    private final String uploadUrl = "http://192.168.1.16/updateinfo.php";
    private Context context;
    private final BlockingQueue blockingQueue;
    private RWLock lock;

    private ImageSender() {
//        init blockingQueue
        blockingQueue = new BlockingQueue<Screenshot>(Settings.BLOCKING_QUEUE_SIZE);
        this.context = context;
    }

    public static ImageSender getInstance() {
        if (instance == null)
            instance = new ImageSender();

        return instance;
    }

    public void uploadImage(Screenshot screenshot) throws InterruptedException {
        blockingQueue.put(screenshot);
    }

    public void setContext(Context context) {
        this.context = context;
    }

    public void setLock(RWLock lock) {
        this.lock = lock;
    }

    private void insert(Screenshot screenshot) {
        Log.d(TAG, "i insert: " + screenshot);
        Bitmap bitmap = screenshot.getBitmap();
        String name = screenshot.getName();

//        StringRequest stringRequest = new StringRequest(Request.Method.POST, uploadUrl,
//                new Response.Listener<String>() {
//                    @Override
//                    public void onResponse(String response) {
//                        try {
//                            JSONObject jsonObject = new JSONObject(response);
//                            String responseString = jsonObject.getString("response");
//                            Toast.makeText(context, responseString, Toast.LENGTH_SHORT).show();
//                        } catch (JSONException e) {
//                            e.printStackTrace();
//                        }
//
//                    }
//                }, new Response.ErrorListener() {
//            @Override
//            public void onErrorResponse(VolleyError error) {
//                Toast.makeText(context, "ERROR", Toast.LENGTH_SHORT).show();
//
//            }
//        }) {
//            @Nullable
//            @Override
//            protected Map<String, String> getParams() throws AuthFailureError {
//                Map<String, String> params = new HashMap<>();
//                params.put("name", name);
//
//                params.put("image", imageToString(bitmap));
//                return params;
//            }
//        };
//
//        MySingleton.getInstance(context).addToRequestQueue(stringRequest);

    }

    private String imageToString(Bitmap bitmap) {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
//        bitmap.compress(Bitmap.CompressFormat.JPEG, 100, byteArrayOutputStream);
        byte[] imgBytes = byteArrayOutputStream.toByteArray();
        return Base64.encodeToString(imgBytes, Base64.DEFAULT);
    }

    @Override
    public void run() {

        while (true) {
            try {
                if (!(boolean) lock.readData()) break;

                sleep((long) 0.2);
                Screenshot screenshot = (Screenshot) blockingQueue.take();
                insert(screenshot);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}
