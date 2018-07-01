package io.sease.rre.core;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.core.domain.metrics.Metric;
import org.junit.Test;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.core.TestData.A_VERSION;
import static io.sease.rre.core.TestData.DOCUMENTS_SETS;
import static java.util.Arrays.stream;
import static org.junit.Assert.assertEquals;

/**
 * Supertype layers for all unit test cases.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class BaseTestCase {
    protected final ObjectMapper mapper = new ObjectMapper();

    protected Metric cut;
    protected AtomicInteger counter;

    /**
     * Returns the class under test.
     *
     * @return the class under test.
     */
    protected Metric cut() {
        return cut;
    }

    /**
     * Setup fixture for this test case.
     */
    public abstract void setUp();

    /**
     * If there are no relevant results and we have an empty resultset, then (symbolic) P is 1.
     */
    @Test
    public void noRelevantDocumentsAndNoSearchResults() {
        cut().setRelevantDocuments(mapper.createObjectNode());
        cut().setTotalHits(0, A_VERSION);

        assertEquals(BigDecimal.ONE, cut().valueFactory(A_VERSION).value());
    }

    /**
     * If there are no relevant results and we haven't an empty resultset, then P should be 0.
     */
    @Test
    public void noRelevantDocumentsWithSearchResults() {
        stream(DOCUMENTS_SETS).forEach(set -> {
            cut().setRelevantDocuments(mapper.createObjectNode());
            cut().setTotalHits(set.length, A_VERSION);

            stream(set)
                    .map(this::searchHit)
                    .forEach(hit -> cut().collect(hit, counter.incrementAndGet(), A_VERSION));

            assertEquals(BigDecimal.ZERO.doubleValue(), cut().valueFactory(A_VERSION).value().doubleValue(), 0);
            setUp();
        });
    }

    /**
     * Creates a JSON object node representation of a document judgment.
     *
     * @param gain the gain that will be associated with the judgment.
     * @return a JSON object node representation of a document judgment.
     */
    protected JsonNode createJudgmentNode(final int gain) {
        final ObjectNode judgment = mapper.createObjectNode();
        judgment.put("gain", gain);
        return judgment;
    }

    /**
     * Generates a search hit used for testing purposes.
     * Note that, for evaluating, we just need the document identifier.
     * That's the reason why the generated document has no other fields.
     *
     * @param id the document identifier.
     * @return a search hit used for testing purposes.
     */
    protected Map<String, Object> searchHit(final String id) {
        final Map<String, Object> doc = new HashMap<>();
        doc.put("id", id);
        return doc;
    }
}