package io.sease.rre.core;

import java.util.Random;

public class TestData {
    static Random RANDOMIZER = new Random();

    public final static String[] FIVE_SEARCH_HITS = {"1", "87", "99", "001", "992"};
    public final static String[] ANOTHER_FIVE_SEARCH_HITS = {"a1", "a87", "a99", "a001", "a992"};
    public final static String[] TEN_SEARCH_HITS = {"1", "87", "99", "001", "992", "15", "875", "995", "0015", "9925"};
    public final static String[] FIFTEEN_SEARCH_HITS = {"1", "87", "99", "001", "992", "15", "875", "995", "0015", "9925", "150", "8750", "9950", "00150", "99250"};

    public final static String[][] DOCUMENTS_SETS = {
            FIVE_SEARCH_HITS,
            ANOTHER_FIVE_SEARCH_HITS,
            TEN_SEARCH_HITS,
            FIFTEEN_SEARCH_HITS
    };

    public final static String A_VERSION = "v1.0";

    public static long randomLong() {
        return RANDOMIZER.nextLong();
    }
}
