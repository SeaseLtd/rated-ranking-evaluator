package io.sease.rre.core.domain.metrics.impl;

import static io.sease.rre.Calculator.*;
import io.sease.rre.core.domain.metrics.CompoundMetric;
import io.sease.rre.core.domain.metrics.Metric;

import java.math.BigDecimal;

/**
 * Mean average precision for a set of queries is the mean of the average precision scores for each query.
 *
 * @author agazzarini
 * @since 1.0
 */
public class MAP extends CompoundMetric {
    /**
     * Builds a new MAP metric.
     */
    public MAP() {
        super(metric -> AveragePrecision.NAME.equals(metric.getName()), "MAP");
    }

    @Override
    public BigDecimal value() {
        if (metrics.size() == 0) return BigDecimal.ZERO;
        return divide(
                metrics.stream().map(Metric::value).reduce(BigDecimal.ZERO, BigDecimal::add),
                metrics.size());
    }
}
