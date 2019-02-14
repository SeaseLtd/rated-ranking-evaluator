package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.annotation.JsonProperty;
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
 * @author worleydl 
 */
public class RecallAtK extends Metric {
    private final int k;

    /**
     * Builds a new Recall at K metric.
     *
     * @param k the recallbound
     */
    public RecallAtK(@JsonProperty("k") final int k) {
        super("R@" + k);
        this.k = k;
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            final AtomicInteger relevantItemsFound = new AtomicInteger();

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                if (rank <= k && judgment(id(hit)).isPresent()){
                    relevantItemsFound.incrementAndGet();
                }
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
