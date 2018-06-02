package io.sease.rre.core.domain.metrics;

import java.util.Map;

/**
 * An object which collects search hits through an iterative process.
 * The concrete implementor declares an interface who allows to be notified
 * when a given search hit is made available.
 *
 * @author agazzarini
 * @since 1.0
 */
public interface HitsCollector {
    /**
     * Consumes the "hit availability" event.
     *
     * @param hit the search hit.
     * @param rank the hit rank.
     */
    void collect(Map<String, Object> hit, int rank, String version);

    /**
     * Sets the total hits (i.e. the total number of results) of the query response associated with this metric.
     *
     * @param totalHits the total hits of the query response associated with this metric.
     */
    void setTotalHits(long totalHits, String version);
}