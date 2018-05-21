package io.sease.rre.core.domain;

import io.sease.rre.core.domain.metrics.Metric;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

/**
 * An evaluation (i.e. a set of measures / metrics) at query-level.
 *
 * @author agazzarini
 * @since 1.0
 */
public class QueryEvaluation {
    private final String query;

    private List<Metric> metrics = new ArrayList<>();

    public QueryEvaluation(final String query) {
        this.query = query;
    }

    public void addAll(final List<Metric> data) {
        metrics.addAll(data);
    }

    public Stream<Metric> stream() {
        return metrics.stream();
    }

    public String getQuery() {
        return query;
    }

    public List<Metric> getMetrics() {
        return metrics;
    }
}
