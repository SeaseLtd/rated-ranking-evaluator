package io.sease.rre.search.api;

import java.util.List;
import java.util.Map;

import static java.util.Collections.unmodifiableList;

/**
 * This is the result of a query / search execution.
 *
 * @author agazzarini
 * @since 1.0
 */
public class QueryOrSearchResponse {
    private final long totalHits;
    private final List<Map<String, Object>> hits;

    /**
     * Builds a new response with the given data.
     *
     * @param totalHits the total hits of this response.
     * @param hits      the current hits window.
     */
    public QueryOrSearchResponse(final long totalHits, final List<Map<String, Object>> hits) {
        this.totalHits = totalHits;
        this.hits = unmodifiableList(hits);
    }

    /**
     * Returns the total hits number associated with this response.
     *
     * @return the total hits number associated with this response.
     */
    public long totalHits() {
        return totalHits;
    }

    /**
     * Returns the current hits window.
     *
     * @return the current hits window.
     */
    public List<Map<String, Object>> hits() {
        return hits;
    }
}