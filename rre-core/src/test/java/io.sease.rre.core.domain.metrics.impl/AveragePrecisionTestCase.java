package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.core.BaseTestCase;
import org.junit.Before;
import org.junit.Test;

import java.math.BigDecimal;

import static io.sease.rre.core.TestData.*;
import static java.util.Arrays.stream;
import static org.junit.Assert.assertEquals;

/**
 * Average Precision Test Case.
 *
 * @author agazzarini
 * @since 1.0
 */
public class AveragePrecisionTestCase extends BaseTestCase {
    /*private AveragePrecision cut;

    *//**
     * Setup fixture for this test case.
     *//*
    @Before
    public void setUp() {
        cut = new AveragePrecision();
    }

    *//**
     * If there are no relevant results and we have an empty resultset, then (symbolic) AP is 1.
     *//*
    @Test
    public void noRelevantDocumentsAndNoSearchResults() {
        cut.setRelevantDocuments(mapper.createObjectNode());
        cut.setTotalHits(0);

        assertEquals(BigDecimal.ONE, cut.valueFactory());
    }

    *//**
     * If there are no relevant results and we haven't an empty resultset, then AP should be 0.
     *//*
    @Test
    public void noRelevantDocumentsWithSearchResults() {
        stream(DOCUMENTS_SETS).forEach(set -> {
            cut.setRelevantDocuments(mapper.createObjectNode());
            cut.setTotalHits(set.length);

            stream(set)
                    .map(this::searchHit)
                    .forEach(cut::collect);

            assertEquals(BigDecimal.ZERO.doubleValue(), cut.valueFactory().value().doubleValue(), 0);
            cut = new AveragePrecision();
        });
    }

    *//**
     * If all results in the window are relevant, then the AP is 1.
     *//*
    @Test
    public void maximumAveragePrecision() {
        stream(DOCUMENTS_SETS).forEach(set -> {
            final ObjectNode judgements = mapper.createObjectNode();
            stream(set).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));

            cut.setRelevantDocuments(judgements);
            cut.setTotalHits(set.length);

            stream(set)
                    .map(this::searchHit)
                    .forEach(cut::collect);

            assertEquals(
                    "Fail to assert dataset with " + set.length + "items.",
                    BigDecimal.ONE.doubleValue(),
                    cut.valueFactory().value().doubleValue(),
                    0);
            cut = new AveragePrecision();
        });
    }

    *//**
     * If no results in the window are relevant, then the AP is 0.
     *//*
    @Test
    public void minimumAveragePrecision() {
        stream(DOCUMENTS_SETS).forEach(set -> {
            final ObjectNode judgements = mapper.createObjectNode();
            stream(set).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));

            cut.setRelevantDocuments(judgements);
            cut.setTotalHits(set.length);

            stream(set)
                    .map(docid -> docid + "_SUFFIX") // make sure this id is not in the set
                    .map(this::searchHit)
                    .forEach(cut::collect);

            assertEquals(BigDecimal.ZERO.doubleValue(), cut.valueFactory().value().doubleValue(), 0);
            cut = new AveragePrecision();
        });
    }

    *//**
     * Scenario: 10 judgments, 15 search results, 10 relevant results in top positions.
     *//*
    @Test
    public void _10_judgments_15_search_results_10_relevant_results_at_top() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(10).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(FIFTEEN_SEARCH_HITS.length);
        stream(FIFTEEN_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(cut::collect);

        assertEquals(
                BigDecimal.ONE.doubleValue(),
                cut.valueFactory().value().doubleValue(),
                0);
    }

    *//**
     * Scenario: 10 judgments, 15 search results, 5 relevant results in top positions.
     *//*
    @Test
    public void _10_judgments_15_search_results_5_relevant_results_at_top() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(10).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(15);
        stream(FIVE_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(cut::collect);

        stream(TEN_SEARCH_HITS)
                .map(docid -> docid + "_SUFFIX")
                .map(this::searchHit)
                .forEach(cut::collect);

        assertEquals(
                (1 / 10d) * 5,
                cut.valueFactory().value().doubleValue(),
                0);
    }

    *//**
     * Scenario: 10 judgments, 15 search results, 5 relevant results in top positions.
     *//*
    @Test
    public void _10_judgments_15_search_results_5_relevant_results_in_the_middle() {
        final ObjectNode judgements = mapper.createObjectNode();
        stream(FIFTEEN_SEARCH_HITS).limit(10).forEach(docid -> judgements.set(docid, createJudgmentNode(3)));
        cut.setRelevantDocuments(judgements);

        cut.setTotalHits(15);
        stream(FIVE_SEARCH_HITS)
                .map(docid -> docid + "_PRE")
                .map(this::searchHit)
                .forEach(cut::collect);

        stream(FIVE_SEARCH_HITS)
                .map(this::searchHit)
                .forEach(cut::collect);

        stream(FIVE_SEARCH_HITS)
                .map(docid -> docid + "_POST")
                .map(this::searchHit)
                .forEach(cut::collect);

        assertEquals(
                0.1772,
                cut.valueFactory().value().doubleValue(),
                0);
    }*/
}