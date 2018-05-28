package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.core.TestData;
import org.junit.Before;
import org.junit.Test;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Stream;

import static java.util.Arrays.stream;
import static org.junit.Assert.assertEquals;

/**
 * Reciprocal Rank Test Case.
 *
 * @author agazzarini
 * @since 1.0
 */
public class ReciprocalRankTestCase {

    private final ObjectMapper mapper = new ObjectMapper();
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

        Stream.of("1", "10", "100", "1000")
                .map(this::searchHit)
                .forEach(cut::collect);

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

    /**
     * If the search produced more than one result, the first result is the only item in the relevant document list,
     * then the RR must be 1.
     */
    @Test
    public void firstRelevantResultAtFirstPosition() {
        final String relevantDocumentId = "3";

        final String [] documents = {relevantDocumentId, "4","8","9","991","98","245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(2));
        judgements.set("5", createJudgmentNode(3));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length);

        stream(documents)
                .map(this::searchHit)
                .forEach(cut::collect);

        assertEquals(BigDecimal.ONE, cut.value().setScale(0));
    }

    /**
     * If the search produced more than one result, the first result is the item in the relevant document list with
     * a max gain, then the RR must be 1.
     */
    @Test
    public void firstMaxRelevantResultAtFourthPosition() {
        final String relevantDocumentId = "3";

        final String [] documents = {"5","8","9",relevantDocumentId,"991","98","245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(3));
        judgements.set("5", createJudgmentNode(1));
        judgements.set("8", createJudgmentNode(1));
        judgements.set("991", createJudgmentNode(1));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length);

        stream(documents)
                .map(this::searchHit)
                .forEach(cut::collect);

        assertEquals(new BigDecimal(1/4d).setScale(2), cut.value().setScale(2));
    }

    /**
     * If the search produced more than one result, the first result is the item in the relevant document list with
     * a max gain, then the RR must be 1.
     */
    @Test
    public void firstMaxRelevantResultAtFirstPosition() {
        final String relevantDocumentId = "3";

        final String [] documents = {relevantDocumentId, "5","8","9","991","98","245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(3));
        judgements.set("5", createJudgmentNode(2));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length);

        stream(documents)
                .map(this::searchHit)
                .forEach(cut::collect);

        assertEquals(BigDecimal.ONE, cut.value().setScale(0));
    }

    /**
     * If the search produced more than one result, the second result is the item in the relevant document list with
     * a max gain, then the RR must be 0.5.
     */
    @Test
    public void firstMaxRelevantResultAtSecondPosition() {
        final String relevantDocumentId = "3";

        final String [] documents = {"5",relevantDocumentId, "8","9","991","98","245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(3));
        judgements.set("5", createJudgmentNode(2));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length);

        stream(documents)
                .map(this::searchHit)
                .forEach(cut::collect);

        assertEquals(new BigDecimal(0.5), cut.value().setScale(1));
    }

    /**
     * If the search produced more than one result, the 2nd result is the only item in the relevant document list,
     * then the RR must be 0.5.
     */
    @Test
    public void firstRelevantResultAtSecondPosition() {
        final String relevantDocumentId = "3";

        final String [] documents = {"4",relevantDocumentId, "8","9","991","98","245"};

        final ObjectNode judgements = mapper.createObjectNode();
        judgements.set(relevantDocumentId, createJudgmentNode(2));
        judgements.set("5", createJudgmentNode(3));

        cut.setRelevantDocuments(judgements);
        cut.setTotalHits(documents.length);

        stream(documents)
                .map(this::searchHit)
                .forEach(cut::collect);

        assertEquals(new BigDecimal(0.5), cut.value().setScale(1));
    }

    private JsonNode createJudgmentNode(final int gain) {
        final ObjectNode judgment = mapper.createObjectNode();
        judgment.put("gain", gain);
        return judgment;
    }

    private Map<String, Object> searchHit(final String id) {
        final Map<String, Object> doc = new HashMap<>();
        doc.put("id", id);
        return doc;
    }
}