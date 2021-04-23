package com.example.tappingbot.model;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public class StopScreenshot {
    private final ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();
    private final Lock readLock = rwLock.readLock();
    private final Lock writeLock = rwLock.writeLock();
    private boolean isStopped;

    public void takeReadLock() throws InterruptedException {

        readLock.lock();
    }

    public void leaveReadLock() {

        readLock.unlock();
    }

    public boolean isStoppedWithLock() throws InterruptedException {

        readLock.lock();
        try {
            return isStopped;
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

    public void stopWithLock(boolean stopValue) throws InterruptedException {
        writeLock.lock();
        try {
            isStopped = stopValue;
        } finally {
            writeLock.unlock();
        }
    }

    public void stop(boolean stopValue) {
        isStopped = stopValue;
    }

    public boolean isStopped() {
        return isStopped;
    }


}
