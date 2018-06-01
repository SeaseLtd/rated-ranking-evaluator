package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.domain.metrics.HitsCollector;
import io.sease.rre.core.domain.metrics.Metric;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * An evaluation (i.e. a set of measures / metrics) at query-level.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Query extends DomainMember implements HitsCollector {
    @JsonProperty("metrics")
    private List<Metric> metrics = new ArrayList<>();

    @Override
    public DomainMember setName(final String query) {
        return super.setName(query);
    }

    @Override
    @JsonProperty("query")
    public String getName() {
        return super.getName();
    }

    /**
     * Adds to this {@link ConfigurationVersion} the given list of metrics.
     * Note that at this stage the metrics are empty, without data and valueFactory.
     *
     * @param metrics the metric instances associated with this instance.
     */
    public void prepare(final List<Metric> metrics) {
        this.metrics.addAll(metrics);
    }

    @Override
    public void setTotalHits(final long totalHits, final String version) {
        metrics.forEach(metric -> metric.setTotalHits(totalHits, version));
    }

    @Override
    public void collect(final Map<String, Object> hit, final int rank, final String version) {
        metrics.forEach(metric -> metric.collect(hit, rank, version));
    }

    @Override
    @JsonIgnore
    public List getChildren() {
        return super.getChildren();
    }
}
