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

import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.core.BaseTestCase;
import org.junit.Before;
import org.junit.Test;

import java.util.Collections;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.core.TestData.A_VERSION;
import static io.sease.rre.core.TestData.TEN_SEARCH_HITS;
import static java.util.Arrays.stream;
import static org.junit.Assert.assertEquals;

/**
 * Precision@2 Test Case.
 *
 * @author agazzarini
 * @since 1.0
 */
public class PrecisionAtTwoTestCase extends BaseTestCase {
    /**
     * Setup fixture for this test case.
     */
    @Before
    public void setUp() {
        cut = new PrecisionAtTwo();
        cut.setVersions(Collections.singletonList(A_VERSION));
        counter = new AtomicInteger(0);
    }

    /**
     * If all results in the window are relevant, then the precision is 1.
     */
    @Test
    public void maximumPrecision() {
       maximum();
    }

    /**
     * Both first and second relevant results.
     */
    @Test
    public void _5_judgments_10_search_results_5_relevant_results_at_top() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(TEN_SEARCH_HITS).limit(5).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(TEN_SEARCH_HITS.length, A_VERSION);
        stream(TEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(
                1,
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0.001);
    }

    /**
     * Only the 1st relevant result.
     */
    @Test
    public void _only_1st_relevant_result() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(TEN_SEARCH_HITS).limit(1).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(TEN_SEARCH_HITS.length, A_VERSION);
        stream(TEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(
                0.5,
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0.001);
    }

    /**
     * Only the 2nd relevant result.
     */
    @Test
    public void _only_2nd_relevant_result() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(TEN_SEARCH_HITS).skip(1).limit(1).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(TEN_SEARCH_HITS.length, A_VERSION);
        stream(TEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(
                0.5,
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0.001);
    }
}