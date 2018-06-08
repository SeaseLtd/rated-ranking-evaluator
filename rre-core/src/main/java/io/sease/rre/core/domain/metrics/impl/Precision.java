package io.sease.rre.core.domain.metrics.impl;

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.Calculator.divide;

/**
 * AveragePrecision is the fraction of the documents retrieved that are relevant to the user's information need.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Precision extends Metric {
    /**
     * Builds a new AveragePrecision metric.
     */
    public Precision() {
        super("P");
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
                if (totalHits == 0) { return relevantDocuments.size() ==0 ? BigDecimal.ONE : BigDecimal.ZERO; }
                return divide(new BigDecimal(relevantItemsFound.get()), totalHits);
            }
        };
    }
}
