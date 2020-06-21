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
package io.sease.rre.core.domain.metrics.impl;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * A test case to ensure that the AveragedMetric handles multi-threaded
 * collect() calls as expected.
 *
 * @author Matt Pearce (matt@elysiansoftware.co.uk)
 */
public class AveragedMetricMultiThreadTestCase {

    private static final int NUM_THREADS = 8;

    private List<String> versions;

    @Before
    public void initialiseVersions() {
        versions = new ArrayList<>();
        for (int i = 0; i < (Math.random() * 100); i ++) {
            versions.add("" + i);
        }
    }

    @After
    public void tearDownVersions() {
        versions = null;
    }

    @Test
    public void singleThreadTest() {
        AveragedMetric am = new AveragedMetric("test");
        for (String v : versions) {
            am.collect(v, BigDecimal.ONE);
        }

        assertThat(am.getVersions().keySet()).containsAll(versions);
    }

    @Test
    public void multiThreadTest() throws Exception {
        AveragedMetric am = new AveragedMetric("test");

        ExecutorService executorService = Executors.newFixedThreadPool(NUM_THREADS);
        Collection<Future<?>> futures = versions.stream()
                .map(v -> new Thread(() -> am.collect(v, BigDecimal.ONE)))
                .map(executorService::submit)
                .collect(Collectors.toList());
        for (Future<?> f : futures) {
            if (!f.isDone()) {
                Thread.sleep(10);
            }
        }

        assertThat(am.getVersions().keySet()).containsAll(versions);
    }
}
