/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package io.sease.rre.core;

import java.util.Random;

public class TestData {
    static Random RANDOMIZER = new Random();

    public final static String[] FIVE_SEARCH_HITS = {"1", "87", "99", "001", "992"};
    public final static String[] ANOTHER_FOUR_SEARCH_HITS = {"1dd", "aa87", "xyz99", "sdas001"};
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
