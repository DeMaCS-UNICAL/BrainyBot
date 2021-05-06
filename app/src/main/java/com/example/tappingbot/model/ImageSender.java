package com.example.tappingbot.model;

import android.content.Context;
import android.graphics.Bitmap;
import android.net.Uri;
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
    private static ImageSender instance;
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

    public void uploadImage(Uri uri) throws InterruptedException {
        blockingQueue.put(uri);
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

//        try {
        //getting bitmap object from uri
//            Bitmap bitmap = MediaStore.Images.Media.getBitmap(context.getContentResolver(), imageUri);

        //calling the method uploadBitmap to upload image
        uploadBitmap(screenshot);
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
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
//                long imagename = System.currentTimeMillis();
                params.put("pic", new DataPart(screenshot.getName() + ".png", getFileDataFromDrawable(screenshot.getBitmap())));
                return params;
            }
        };

        //adding the request to volley
        Volley.newRequestQueue(context).add(volleyMultipartRequest);
    }


    @Override
    public void run() {

        while (true) {
            try {
                if (!(boolean) lock.readData()) break;

                sleep((long) 0.2);
//                Uri screenshot = (Uri) blockingQueue.take();
                Screenshot screenshot = (Screenshot) blockingQueue.take();
                insert(screenshot);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}
