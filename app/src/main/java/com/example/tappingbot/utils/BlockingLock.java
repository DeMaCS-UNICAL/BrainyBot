package com.example.tappingbot.utils;

import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class BlockingLock<T> {

    private final Lock lock = new ReentrantLock();
    private final Condition full_condition = lock.newCondition();
    private final Condition empty_condition = lock.newCondition();

    private T elem;

    public BlockingLock() {
        elem = null;
    }

    public void put(final T c) throws InterruptedException {

        lock.lock();
        try {
            while (elem != null)
                try {
                    full_condition.await();
                } catch (final InterruptedException e) {
                    e.printStackTrace();
                }

            elem = c;
            empty_condition.signal();

        } finally {
            lock.unlock();
        }

    }

    public T take() throws InterruptedException {

        T returnValue;
        lock.lock();
        try {
            while (elem == null)
                try {
                    empty_condition.await();
                } catch (final InterruptedException e) {
                    e.printStackTrace();
                }

            returnValue = elem;
            elem = null;
            full_condition.signal();
            return returnValue;
        } finally {
            lock.unlock();
        }
    }
}
