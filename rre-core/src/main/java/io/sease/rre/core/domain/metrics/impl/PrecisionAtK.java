package io.sease.rre.core.domain.metrics.impl;

import io.sease.rre.core.domain.metrics.RankMetric;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;

public class PrecisionAtK extends RankMetric {
    private final int k;

    PrecisionAtK(final int k) {
        super("P@" + k);
        this.k = k;
    }

    @Override
    public BigDecimal value() {
        if (totalHits == 0) { return BigDecimal.ZERO; }
        return hits.stream()
                .map(hit -> BigDecimal.ONE)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .divide(totalHits > k ? new BigDecimal(k) : new BigDecimal(totalHits), 2, RoundingMode.HALF_UP);
    }

    @Override
    public void accumulate(final Map<String, Object> hit, final int rank) {
        if (rank <= k) {
            hits.add(hit);
        }
    }
}