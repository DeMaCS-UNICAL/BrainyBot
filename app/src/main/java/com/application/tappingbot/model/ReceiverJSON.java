package com.application.tappingbot.model;

import android.annotation.SuppressLint;
import android.content.Context;
import android.util.Log;

import com.android.volley.Request;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonArrayRequest;
import com.application.tappingbot.controller.JSONSingleton;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public class ReceiverJSON {

    private static final String TAG = "ReceiverJSON";
    @SuppressLint("StaticFieldLeak")
    private static Context context;
    @SuppressLint("StaticFieldLeak")
    private static ReceiverJSON instance;

    private ReceiverJSON() {
    }

    public static ReceiverJSON getInstance() throws Exception {

        if (context == null)
            throw new Exception("context == null");

        if (instance == null)
            instance = new ReceiverJSON();

        return instance;
    }

    public static void setContext(Context context) {
        ReceiverJSON.context = context;
    }
    
    public void request(String url) {
        JsonArrayRequest jsonArrayRequest = new JsonArrayRequest
                (Request.Method.GET, url, null, new Response.Listener<JSONArray>() {

                    @Override
                    public void onResponse(JSONArray response) {

                        for (int i = 0; i < response.length(); ++i) {
                            try {
                                JSONObject jsonObject = response.getJSONObject(i);
                                Log.d(TAG, "Response n." + i + " : " + jsonObject.toString());
                            } catch (JSONException e) {
                                e.printStackTrace();
                            }

                        }

                    }

                }, new Response.ErrorListener() {

                    @Override
                    public void onErrorResponse(VolleyError error) {
                        // TODO: Handle error
                        Log.e(TAG, "Error: " + error.toString());
                    }
                });


        // Access the RequestQueue through your singleton class.
        JSONSingleton.getInstance(context).addToRequestQueue(jsonArrayRequest);
    }
}
