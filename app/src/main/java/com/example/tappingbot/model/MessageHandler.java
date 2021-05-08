package com.example.tappingbot.model;

import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.Socket;

public class MessageHandler {
    public static String ERROR = "ERROR";
    public static String TAKE_SCREENSHOT_NOW = "TAKE SCREENSHOT NOW";
    private static Socket socket;
    private static ObjectInputStream in;
    private static ObjectOutputStream out;

    public static void connect(String host, int port) throws Exception {
        if (socket != null)
            return;
        socket = new Socket(host, port);
        out = new ObjectOutputStream(socket.getOutputStream());
    }

    public static String read() throws Exception {
        if (socket == null)
            return ERROR;
        if (in == null)
            in = new ObjectInputStream(socket.getInputStream());
        return (String) in.readObject();
    }

    public static void sendMessage(String message) throws Exception {
        if (out == null)
            return;
        out.writeObject(message);
        out.flush();
    }
}