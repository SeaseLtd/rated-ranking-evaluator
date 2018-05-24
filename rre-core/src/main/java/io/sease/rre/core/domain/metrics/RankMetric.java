package io.sease.rre.core.domain.metrics;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * A metric which needs to be aware about the ranking of collected hits.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class RankMetric extends Metric {
    private final AtomicInteger rank = new AtomicInteger();
    protected List<Map<String, Object>> hits = new ArrayList<>();

    /**
     * Builds a new {@link Metric} with the given mnemonic name.
     *
     * @param name the metric name.
     */
    public RankMetric(final String name) {
        super(name);
    }

    @Override
    public final void collect(final Map<String, Object> hit) {
        collect(hit, rank.incrementAndGet());
    }

    /**
     * Template method which adds the rank to the {@link HitsCollector}'s method signature.
     *
     * @param hit the search hit.
     * @param rank the hit rank.
     */
    public abstract void collect(Map<String, Object> hit, int rank);
}
