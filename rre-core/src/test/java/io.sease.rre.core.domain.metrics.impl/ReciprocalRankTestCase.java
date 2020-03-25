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
import io.sease.rre.core.domain.metrics.Metric;
import org.junit.Before;
import org.junit.Test;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.core.TestData.A_VERSION;
import static io.sease.rre.core.TestData.FIFTEEN_SEARCH_HITS;
import static java.util.Arrays.stream;
import static org.junit.Assert.assertEquals;

/**
 * Reciprocal Rank Test Case.
 *
 * @author agazzarini
 * @since 1.0
 */
public class ReciprocalRankTestCase extends BaseTestCase {
    /**
     * Setup fixture for this test case.
     */
    @Before
    @Override
    public void setUp() {
        cut = new ReciprocalRank();
        cut.setVersions(Collections.singletonList(A_VERSION));
        counter = new AtomicInteger();
    }

    @Test
    public void minimumResultsMatchesK() {
        assertEquals(Metric.DEFAULT_REQUIRED_RESULTS, cut.getRequiredResults());
    }

    /**
     * If the search produced more than one result, the first result is the only item in the relevant document list,
     * then the RR must be 1.
     */
    @Test
    public void firstRelevantResultAtFirstPosition() {
        final String relevantDocumentId = "3";

        final String[] documents = {relevantDocumentId, "4", "8", "9", "991", "98", "245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(2));
        judgements.set("5", createJudgmentNode(3));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length, A_VERSION);

        stream(documents)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(BigDecimal.ONE.doubleValue(), cut.valueFactory(A_VERSION).value().doubleValue(), 0);
    }

    /**
     * If the search produced more than one result, the first result is the item in the relevant document list with
     * a max gain, then the RR must be 1.
     */
    @Test
    public void firstMaxRelevantResultAtFourthPosition() {
        final String relevantDocumentId = "3";

        final String[] documents = {"5", "8", "9", relevantDocumentId, "991", "98", "245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(3));
        judgements.set("5", createJudgmentNode(1));
        judgements.set("8", createJudgmentNode(1));
        judgements.set("991", createJudgmentNode(1));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length, A_VERSION);

        stream(documents)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(1 / 4d, cut.valueFactory(A_VERSION).value().doubleValue(), 0);
    }

    /**
     * If the search produced more than one result, the first result is the item in the relevant document list with
     * a max gain, then the RR must be 1.
     */
    @Test
    public void firstMaxRelevantResultAtFirstPosition() {
        final String relevantDocumentId = "3";

        final String[] documents = {relevantDocumentId, "5", "8", "9", "991", "98", "245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(3));
        judgements.set("5", createJudgmentNode(2));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length, A_VERSION);

        stream(documents)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(BigDecimal.ONE.doubleValue(), cut.valueFactory(A_VERSION).value().doubleValue(), 0);
    }

    /**
     * If the search produced more than one result, the second result is the item in the relevant document list with
     * a max gain, then the RR must be 0.5.
     */
    @Test
    public void firstMaxRelevantResultAtSecondPosition() {
        final String relevantDocumentId = "3";

        final String[] documents = {"5", relevantDocumentId, "8", "9", "991", "98", "245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(3));
        judgements.set("5", createJudgmentNode(2));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length, A_VERSION);

        stream(documents)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(0.5d, cut.valueFactory(A_VERSION).value().doubleValue(), 0);
    }

    /**
     * If the search produced more than one result, the 2nd result is the only item in the relevant document list,
     * then the RR must be 0.5.
     */
    @Test
    public void firstRelevantResultAtSecondPosition() {
        final String relevantDocumentId = "3";

        final String[] documents = {"4", relevantDocumentId, "8", "9", "991", "98", "245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(2));
        judgements.set("5", createJudgmentNode(3));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length, A_VERSION);

        stream(documents)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(0.5d, cut.valueFactory(A_VERSION).value().doubleValue(), 0);
    }

    /**
     * If the first relevant result is outside the first K results, the value
     * should be 0.
     */
    @Test
    public void firstRelevantResultOutsideKResults() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).skip(11).limit(1).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(FIFTEEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(0.0d, cut.valueFactory(A_VERSION).value().doubleValue(), 0);
    }
}