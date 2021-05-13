package com.example.tappingbot.utils;

public class Settings {
    public static final int REQUEST_CODE = 100;
    public static final int BLOCKING_QUEUE_SIZE = 100;
    public static final int POOL_SIZE = 1;


    public static final int PORT = 8000;
    public static final String HOST = "192.168.1.16";
    public static final String ROOT_URL = "http://" + HOST + "/updateinfo.php?apicall=";


    public static final String UPLOAD_URL = ROOT_URL + "uploadpic";
    public static final String GET_PICS_URL = ROOT_URL + "getpics";
    public static int localHostServerPort = 5000;
}
