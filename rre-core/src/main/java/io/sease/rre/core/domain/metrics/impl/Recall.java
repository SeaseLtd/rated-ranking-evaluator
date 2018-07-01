package io.sease.rre.core.domain.metrics.impl;

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.Calculator.divide;

/**
 * Recall is the fraction of the documents that are relevant to the query that are successfully retrieved.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Recall extends Metric {
    /**
     * Builds a new Recall at X metric.
     */
    public Recall() {
        super("R");
    }

    @Override
    public ValueFactory valueFactory() {
        return new ValueFactory(this) {
            final AtomicInteger relevantItemsFound = new AtomicInteger();

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                judgment(id(hit)).ifPresent(relevantItem -> relevantItemsFound.incrementAndGet());
            }

            @Override
            public BigDecimal value() {
                if (relevantDocuments.size() == 0) {
                    return totalHits == 0 ? BigDecimal.ONE : BigDecimal.ZERO;
                }
                return divide(new BigDecimal(relevantItemsFound.get()), relevantDocuments.size());
            }
        };
    }
}