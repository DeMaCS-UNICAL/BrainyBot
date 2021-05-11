package com.example.tappingbot.utils;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public class RWLock<T> {
    private final ReentrantReadWriteLock readWriteLock = new ReentrantReadWriteLock();
    private final Lock readLock = readWriteLock.readLock();
    private final Lock writeLock = readWriteLock.writeLock();

    private T data;

    public RWLock(T data) {
        this.data = data;
    }

    public RWLock() {
    }

    public void takeReadLock() throws InterruptedException {
        readLock.lock();
    }

    public void leaveReadLock() {
        readLock.unlock();
    }

    // takeReadLock() + leaveReadLock()
    public T readData() throws InterruptedException {

        readLock.lock();
        try {
            return data;
        } finally {
            readLock.unlock();
        }
    }

    public void takeWriteLock() throws InterruptedException {
        writeLock.lock();
    }

    public void leaveWriteLock() {
        writeLock.unlock();
    }

    // takeWriteLock() + leaveWriteLock()
    public void writeData(T d) throws InterruptedException {
        writeLock.lock();
        try {
            data = d;
        } finally {
            writeLock.unlock();
        }

    }

    public T getData() {
        return data;
    }

    public void setData(T i) {
        data = i;
    }
}
