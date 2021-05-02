package com.example.tappingbot.model;

import android.graphics.Bitmap;

import java.util.Objects;

public class Screenshot {
    private Bitmap bitmap;
    private String name;

    public Screenshot(Bitmap bitmap, String name) {
        this.bitmap = bitmap;
        this.name = name;
    }

    public Bitmap getBitmap() {
        return bitmap;
    }

    public void setBitmap(Bitmap bitmap) {
        this.bitmap = bitmap;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Screenshot)) return false;
        Screenshot that = (Screenshot) o;
        return Objects.equals(getBitmap(), that.getBitmap()) &&
                Objects.equals(getName(), that.getName());
    }

    @Override
    public int hashCode() {
        return Objects.hash(getBitmap(), getName());
    }

    @Override
    public String toString() {
        return "Screenshot{" +
                "bitmap=" + bitmap +
                ", name='" + name + '\'' +
                '}';
    }
}
