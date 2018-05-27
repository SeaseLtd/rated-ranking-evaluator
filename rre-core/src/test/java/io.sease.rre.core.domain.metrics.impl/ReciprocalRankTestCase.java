package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.core.TestData;
import org.junit.Before;
import org.junit.Test;

import java.math.BigDecimal;
import java.util.AbstractMap;
import java.util.HashMap;
import java.util.Map;

import static java.util.stream.IntStream.range;
import static org.junit.Assert.assertEquals;

/**
 * Reciprocal Rank Test Case.
 *
 * @author agazzarini
 * @since 1.0
 */
public class ReciprocalRankTestCase {

    final ObjectMapper mapper = new ObjectMapper();
    private ReciprocalRank cut;

    /**
     * Setup fixture for this test case.
     */
    @Before
    public void setUp() {
        cut = new ReciprocalRank();
    }

    /**
     * If there are no relevant results in the resultset, then RR must be 0.
     */
    @Test
    public void noRelevantResults() {
        // having empty judgements in this case is equal to having no relevant judgment matchings
        cut.setRelevantDocuments(mapper.createObjectNode());

        cut.setTotalHits(TestData.randomLong());

        final String [] docids = {"1", "10", "100", "1000"};
        range(0, docids.length)
                .mapToObj(index -> new AbstractMap.SimpleEntry<>(docids[index], index))
                .map(this::searchHit)
                .forEach(searchHit -> cut.collect(searchHit, (Integer)searchHit.get("rank")));

        assertEquals(BigDecimal.ZERO, cut.value());
    }

    /**
     * If there are no expected results, then RR must be 1.
     */
    @Test
    public void zeroExpectedResults() {
        cut.setRelevantDocuments(mapper.createObjectNode());
        cut.setTotalHits(0);

        assertEquals(BigDecimal.ONE, cut.value());
    }

    private JsonNode createJudgmentNode(final int gain) {
        final ObjectNode judgment = mapper.createObjectNode();
        judgment.put("gain", gain);
        return judgment;
    }

    private Map<String, Object> searchHit(AbstractMap.SimpleEntry<String, Integer> entry) {
        final Map<String, Object> doc = new HashMap<>();
        doc.put("id", entry.getKey());
        doc.put("rank", entry.getValue());
        return doc;
    }
}