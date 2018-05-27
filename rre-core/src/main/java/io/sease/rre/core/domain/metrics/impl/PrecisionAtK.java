package io.sease.rre.core.domain.metrics.impl;

import io.sease.rre.core.domain.metrics.RankMetric;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;

/**
 * Supertype layer for all precision at X metrics.
 *
 * @author agazzarini
 * @since 1.0
 */
public class PrecisionAtK extends RankMetric {
    private final int k;

    /**
     * Builds a new ReciprocalRank at X metric.
     *
     * @param k the precision bound.
     */
    PrecisionAtK(final int k) {
        super("P@" + k);
        this.k = k;
    }

    @Override
    public BigDecimal value() {
        if (totalHits == 0) { return hits.isEmpty() ? BigDecimal.ONE : BigDecimal.ZERO; }
        return hits.stream()
                .map(hit -> BigDecimal.ONE)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .divide(new BigDecimal(Math.min(totalHits, k)), 2, RoundingMode.HALF_UP);
    }

    @Override
    public void collect(final Map<String, Object> hit, final int rank) {
        if (rank <= k && judgment(id(hit)).isPresent()) {
            hits.add(hit);
        }
    }
}