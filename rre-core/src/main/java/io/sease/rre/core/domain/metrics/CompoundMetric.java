package io.sease.rre.core.domain.metrics;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

public abstract class CompoundMetric {
    protected List<Metric> metrics = new ArrayList<>();
    private final Predicate<Metric> filter;
    private final String name;

    /**
     * Builds a new {@link CompoundMetric} with the given filter.
     *
     * @param filter the filter used for filtering the collected sub-metrics.
     * @param name the metric name.
     */
    public CompoundMetric(final Predicate<Metric> filter, final String name) {
        this.filter = filter;
        this.name = name;
    }

    public void collect(final Metric metric) {
        if (filter.test(metric)) {
            metrics.add(metric);
        }
    }

    public abstract BigDecimal value();

    public String getName() {
        return name;
    }

    public BigDecimal getValue() {
        return value().setScale(4, RoundingMode.CEILING);
    }
}
