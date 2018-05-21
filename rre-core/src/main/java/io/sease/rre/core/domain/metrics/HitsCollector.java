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
@FunctionalInterface
public interface HitsCollector {
    /**
     * Consumes the "hit availability" event.
     *
     * @param hit the search hit.
     */
    void collect(Map<String, Object> hit);
}