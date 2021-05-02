package com.example.tappingbot.utils;

import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class BlockingQueue<T> {

    private final Lock lock = new ReentrantLock();
    private final Condition fullCondition = lock.newCondition();
    private final Condition emptyCondition = lock.newCondition();

    private final T[] theBuffer;
    private int in, out, fullSlot;

    @SuppressWarnings("unchecked")
    public BlockingQueue(final int dim) {

        in = 0;
        out = 0;
        fullSlot = 0;
        theBuffer = (T[]) new Object[dim];
    }

    public void put(final T c) throws InterruptedException {

        lock.lock();
        try {
            while (fullSlot == theBuffer.length)
                try {
                    fullCondition.await();
                } catch (final InterruptedException ignored) {

                }

            theBuffer[in] = c;
            in = (in + 1) % theBuffer.length;
            if (fullSlot == 0)
                emptyCondition.signal();
            fullSlot++;

            // show();
        } finally {
            lock.unlock();
        }

    }

    @SuppressWarnings("unused")
    private void show() {
        final char[] val = new char[theBuffer.length];
        for (int i = 0; i < fullSlot; i++)
            val[(out + i) % theBuffer.length] = '*';
        for (int i = 0; i < theBuffer.length - fullSlot; i++)
            val[(in + i) % theBuffer.length] = '-';
        System.out.print("In:" + in + " Out:" + out + " C:" + fullSlot + " ");
        System.out.println(val);
    }

    public T take() throws InterruptedException {

        T returnValue;
        lock.lock();
        try {
            while (fullSlot == 0)
                try {
                    emptyCondition.await();
                } catch (final InterruptedException e) {
                }

            returnValue = theBuffer[out];
            out = (out + 1) % theBuffer.length;
            if (fullSlot == theBuffer.length)
                fullCondition.signal();
            fullSlot--;
            // show();
            return returnValue;
        } finally {
            lock.unlock();
        }

    }

}
