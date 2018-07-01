package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.core.BaseTestCase;
import org.junit.Before;
import org.junit.Test;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.core.TestData.*;
import static java.util.Arrays.stream;
import static org.junit.Assert.assertEquals;

/**
 * Average AveragePrecision Test Case.
 *
 * @author agazzarini
 * @since 1.0
 */
public class AveragePrecisionTestCase extends BaseTestCase {
    /**
     * Setup fixture for this test case.
     */
    @Before
    public void setUp() {
        cut = new AveragePrecision();
        cut.setVersions(Collections.singletonList(A_VERSION));
        counter = new AtomicInteger(0);
    }

    /**
     * If all results in the window are relevant, then the AP is 1.
     */
    @Test
    public void maximumAveragePrecision() {
        stream(DOCUMENTS_SETS).forEach(set -> {
            final ObjectNode judgements = mapper.createObjectNode();
            stream(set).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));

            cut.setRelevantDocuments(judgements);
            cut.setTotalHits(set.length, A_VERSION);

            stream(set)
                    .map(this::searchHit)
                    .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

            assertEquals(
                    "Fail to assert dataset with " + set.length + "items.",
                    BigDecimal.ONE.doubleValue(),
                    cut.valueFactory(A_VERSION).value().doubleValue(),
                    0);
            setUp();
        });
    }

    /**
     * If no results in the window are relevant, then the AP is 0.
     */
    @Test
    public void minimumAveragePrecision() {
        stream(DOCUMENTS_SETS).forEach(set -> {
            final ObjectNode judgements = mapper.createObjectNode();
            stream(set).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));

            cut.setRelevantDocuments(judgements);
            cut.setTotalHits(set.length, A_VERSION);

            stream(set)
                    .map(docid -> docid + "_SUFFIX") // make sure this id is not in the set
                    .map(this::searchHit)
                    .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

            assertEquals(BigDecimal.ZERO.doubleValue(), cut.valueFactory(A_VERSION).value().doubleValue(), 0);
            setUp();
        });
    }

    /**
     * Scenario: 10 judgments, 15 search results, 10 relevant results in top positions.
     */
    @Test
    public void _10_judgments_15_search_results_10_relevant_results_at_top() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(10).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(FIFTEEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(
                BigDecimal.ONE.doubleValue(),
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0);
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

        assertEquals(
                (1 / 10d) * 5,
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0);
    }

    /**
     * Scenario: 10 judgments, 15 search results, 5 relevant results in top positions.
     */
    @Test
    public void _10_judgments_15_search_results_5_relevant_results_in_the_middle() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(10).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length, A_VERSION);
        stream(FIVE_SEARCH_HITS)
                .map(docid -> docid + "_PRE")
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        stream(FIVE_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        stream(FIVE_SEARCH_HITS)
                .map(docid -> docid + "_POST")
                .map(this::searchHit)
                .forEach(hit -> cut.collect(hit, counter.incrementAndGet(), A_VERSION));

        assertEquals(
                0.1772,
                cut.valueFactory(A_VERSION).value().doubleValue(),
                0);
    }
}