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

import com.carrotsearch.randomizedtesting.RandomizedRunner;
import com.carrotsearch.randomizedtesting.annotations.ParametersFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.core.BaseTestCase;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.core.TestData.ANOTHER_FIVE_SEARCH_HITS;
import static io.sease.rre.core.TestData.ANOTHER_FOUR_SEARCH_HITS;
import static io.sease.rre.core.TestData.A_VERSION;
import static io.sease.rre.core.TestData.FIFTEEN_SEARCH_HITS;
import static io.sease.rre.core.TestData.FIVE_SEARCH_HITS;
import static io.sease.rre.core.TestData.TEN_SEARCH_HITS;
import static java.util.Arrays.stream;
import static java.util.Collections.singletonList;
import static java.util.stream.Collectors.toList;
import static java.util.stream.IntStream.range;
import static org.junit.Assert.assertEquals;

@RunWith(RandomizedRunner.class)
public class NDCGAtKTestCase extends BaseTestCase {

    private final int currentAppliedK;

    public NDCGAtKTestCase(final Integer k) {
        this.currentAppliedK = k;
    }

    /**
     * The {@link Iterable} returned by this method will actually determine the tests cardinality.
     * That is: each (array) element within the returned {@link Iterable} will cause a new method test execution
     * with that array passed as input parameter. Note this will happen *for each* test method in this class.
     */
    @ParametersFactory
    public static Iterable<Object[]> kRange()
    {
        return range(1,11)
                .mapToObj(Collections::singletonList)
                .map(List::toArray)
                .collect(toList());
    }

    @Before
    public void setUp() {
        cut = new NDCGAtK(currentAppliedK);
        cut.setVersions(singletonList(A_VERSION));
        counter = new AtomicInteger(0);
    }

    @Test
    public void minimumResultsMatchesDefault() {
        assertEquals(currentAppliedK, cut.getRequiredResults());
    }

    /**
     * If all results in the window are relevant, then the NDCG is 1.
     */
    @Test
    public void maximumNdcg() {
       maximum();
    }

    /**
     * Scenario: 15 judgments, 15 search results, 10 relevant results in top positions. NDCG = 1
     */
    @Test
    public void _10_judgments_15_search_results_10_relevant_results_at_top() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(currentAppliedK).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(FIFTEEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(
                1,
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0.001);
    }

    /**
     * Scenario: 10 judgments, 15 search results, 5 relevant results in top positions.
     */
    @Test
    public void _10_judgments_15_search_results_5_relevant_results_at_top() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(10).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(FIVE_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        stream(TEN_SEARCH_HITS)
                .map(docid -> docid + "_SUFFIX")
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        Map<Integer, Double> expectations = new HashMap<Integer, Double>()
        {{
            put(1, 1d);
            put(2,1d);
            put(3,1d);
            put(4,1d);
            put(5,1d);
            put(6,0.89);
            put(7,0.81);
            put(8, 0.74);
            put(9,0.69);
            put(10, 0.64);
        }};

        assertEquals(
                expectations.get(currentAppliedK),
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0);
    }

    /**
     * Scenario: 10 judgments, 15 search results, 5 relevant results in top positions.
     */
    @Test
    public void _10_judgments_15_search_results_5_relevant_results_from_5th_to_10th() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).skip(5).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(FIFTEEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        Map<Integer, Double> expectations = new HashMap<Integer, Double>()
        {{
            put(1,0.0);
            put(2,0.0);
            put(3,0.0);
            put(4,0.0);
            put(5,0.0);
            put(6,0.10);
            put(7,0.18);
            put(8, 0.25);
            put(9,0.30);
            put(10, 0.35);
        }};

        assertEquals(
                expectations.get(currentAppliedK),
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0);
    }

    /**
     * Scenario: 10 judgments, 15 search results, 5 relevant results in top positions.
     */
    @Test
    public void _10_judgments_15_search_results_5_relevant_results_various_degree() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).skip(0).forEach(docid -> judgements.set(docid, createJudgmentNode(1)));
        stream(FIFTEEN_SEARCH_HITS).skip(1).forEach(docid -> judgements.set(docid, createJudgmentNode(2)));
        stream(FIFTEEN_SEARCH_HITS).skip(2).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        stream(FIFTEEN_SEARCH_HITS).skip(3).forEach(docid -> judgements.set(docid, createJudgmentNode(4)));
        stream(FIFTEEN_SEARCH_HITS).skip(4).forEach(docid -> judgements.set(docid, createJudgmentNode(2)));
        stream(FIFTEEN_SEARCH_HITS).skip(5).forEach(docid -> judgements.set(docid, createJudgmentNode(0)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(FIFTEEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        Map<Integer, Double> expectations = new HashMap<Integer, Double>()
        {{
            put(1,0.06);
            put(2,0.14);
            put(3,0.3);
            put(4,0.57);
            put(5,0.62);
            put(6,0.62);
            put(7,0.62);
            put(8, 0.62);
            put(9,0.62);
            put(10, 0.62);
        }};

        assertEquals(
                expectations.get(currentAppliedK),
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0);
    }

    /**
     * Scenario: 10 judgments, 15 search results, 5 relevant results in top positions.
     */
    @Test
    public void _10_judgments_15_search_only_results_10th_relevant_result() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(10).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(ANOTHER_FIVE_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        stream(ANOTHER_FOUR_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        cut.collect(searchHit(FIFTEEN_SEARCH_HITS[9]), counter.incrementAndGet(), A_VERSION);

        Map<Integer, Double> expectations = new HashMap<Integer, Double>()
        {{
            put(1,0.0);
            put(2,0.0);
            put(3,0.0);
            put(4,0.0);
            put(5,0.0);
            put(6,0.0);
            put(7,0.0);
            put(8, 0.0);
            put(9,0.0);
            put(10, 0.06);
        }};

        assertEquals(
                expectations.get(currentAppliedK),
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0);
    }

    /**
     * Scenario: 10 judgments, 15 search results, 5 relevant results in top positions.
     */
    @Test
    public void _10_judgments_15_search_only_results_10th_relevant_result_topscore() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(10).forEach(docid -> judgements.set(docid, createJudgmentNode(4)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(ANOTHER_FIVE_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        stream(ANOTHER_FOUR_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        cut.collect(searchHit(FIFTEEN_SEARCH_HITS[9]), counter.incrementAndGet(), A_VERSION);

        Map<Integer, Double> expectations = new HashMap<Integer, Double>()
        {{
            put(1,0.0);
            put(2,0.0);
            put(3,0.0);
            put(4,0.0);
            put(5,0.0);
            put(6,0.0);
            put(7,0.0);
            put(8, 0.0);
            put(9,0.0);
            put(10, 0.06);
        }};

        assertEquals(
                expectations.get(currentAppliedK),
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0);
    }
}
