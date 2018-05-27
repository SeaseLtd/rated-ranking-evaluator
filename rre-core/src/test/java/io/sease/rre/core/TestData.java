package io.sease.rre.core;

import java.util.Random;

public class TestData {
    static Random RANDOMIZER = new Random();

    public static long randomLong() {
        return RANDOMIZER.nextLong();
    }
}
