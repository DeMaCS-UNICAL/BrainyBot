package com.example.tappingbot.model;

import android.content.Context;
import android.graphics.Bitmap;
import android.util.Base64;

import androidx.annotation.Nullable;

import com.android.volley.AuthFailureError;
import com.android.volley.Request;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.StringRequest;
import com.example.tappingbot.controller.MySingleton;

import java.io.ByteArrayOutputStream;
import java.util.HashMap;
import java.util.Map;

public class ImageSender {
    private static ImageSender instance;
    private final String uploadUrl = "http://192.168.1.16/updateinfo.php";
    private Context context;

    private ImageSender() {
    }

    public static ImageSender getInstance() {
        if (instance == null)
            instance = new ImageSender();

        return instance;
    }

    public void setContext(Context context) {
        this.context = context;
    }

    public void uploadImage(Bitmap bitmap, String name) {
        StringRequest stringRequest = new StringRequest(Request.Method.POST, uploadUrl,
                new Response.Listener<String>() {
                    @Override
                    public void onResponse(String response) {
//                        try {
//                            JSONObject jsonObject = new JSONObject(response);
//                            String responseString = jsonObject.getString("response");
//                            Toast.makeText(context, responseString, Toast.LENGTH_SHORT).show();
//                        } catch (JSONException e) {
//                            e.printStackTrace();
//                        }

                    }
                }, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {

            }
        }) {
            @Nullable
            @Override
            protected Map<String, String> getParams() throws AuthFailureError {
                Map<String, String> params = new HashMap<>();
                params.put("name", name);

                params.put("image", imageToString(bitmap));
                return params;
            }
        };

        MySingleton.getInstance(context).addToRequestQueue(stringRequest);

    }

    private String imageToString(Bitmap bitmap) {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
//        bitmap.compress(Bitmap.CompressFormat.JPEG, 100, byteArrayOutputStream);
        byte[] imgBytes = byteArrayOutputStream.toByteArray();
        return Base64.encodeToString(imgBytes, Base64.DEFAULT);
    }

}
