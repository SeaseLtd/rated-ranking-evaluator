package io.sease.rre.core;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.util.HashMap;
import java.util.Map;

/**
 * Supertype layers for all unit test cases.
 *
 * @author agazzarini
 * @since 1.0
 */
public class BaseTestCase {
    protected final ObjectMapper mapper = new ObjectMapper();

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