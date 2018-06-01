package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.domain.metrics.CompoundMetric;
import io.sease.rre.core.domain.metrics.Metric;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

/**
 * A configuration version.
 * Since a configuration is supposed to be immutable, when we change something on it, even a bit,
 * the RRE approach encourages to create a new version, which will be represented by this class.
 * On top of that, when RRE will run, it will compute the configured set of metrics, for each query, for each
 * {@link ConfigurationVersion}.
 *
 * @author agazzarini
 * @since 1.0
 */
public class ConfigurationVersion extends DomainMember {
    @JsonProperty("metrics")
    private List<Metric> metrics = new ArrayList<>();

    @Override
    @JsonIgnore
    public List getChildren() {
        return super.getChildren();
    }

    @Override
    @JsonIgnore
    public Map<String, List<CompoundMetric>> getCompoundMetrics() {
        return super.getCompoundMetrics();
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

    /**
     * Returns a stream of all metrics associated with this {@link ConfigurationVersion}.
     *
     * @return a stream of all metrics associated with this configuration.
     */
    public Stream<Metric> stream() {
        return metrics.stream();
    }
}
