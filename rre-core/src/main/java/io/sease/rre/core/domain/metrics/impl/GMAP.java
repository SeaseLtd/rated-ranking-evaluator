package io.sease.rre.core.domain.metrics.impl;

import io.sease.rre.core.domain.metrics.CompoundMetric;

import java.math.BigDecimal;

public class GMAP extends CompoundMetric {
    /**
     * Builds a new {@link GMAP} metric.
     */
    public GMAP() {
        super(metric -> AveragePrecision.NAME.equals(metric.getName()), "GMAP");
    }

    @Override
    public BigDecimal value() {
        if (metrics.size() == 0) return BigDecimal.ZERO;
        return BigDecimal.valueOf(
                Math.pow(
                    metrics.stream().map(metric -> metric.valueFactory().value()).reduce(BigDecimal.ONE, BigDecimal::multiply).doubleValue(),
                    1.0 / metrics.size()));
    }
}