package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Supertype layer for all precision at X metrics.
 *
 * @author agazzarini
 * @since 1.0
 */
public class PrecisionAtK extends Metric {
    private final int k;

    /**
     * Builds a new AveragePrecision at X metric.
     *
     * @param k the precision bound.
     */
    PrecisionAtK(@JsonProperty("k") final int k) {
        super("P@" + k);
        this.k = k;
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            private final List<Map<String, Object>> collected = new ArrayList<>();

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                if (rank <= k && judgment(id(hit)).isPresent()) {
                    collected.add(hit);
                }
            }

            @Override
            public BigDecimal value() {
                if (totalHits == 0) {
                    return relevantDocuments.size() == 0 ? BigDecimal.ONE : BigDecimal.ZERO;
                }
                return collected.stream()
                        .map(hit -> BigDecimal.ONE)
                        .reduce(BigDecimal.ZERO, BigDecimal::add)
                        .divide(new BigDecimal(Math.min(totalHits, k)), 2, RoundingMode.HALF_UP);
            }
        };
    }
}