package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.domain.metrics.Metric;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

/**
 * A configuration version.
 * Each version is supposed to be a configuration "instance" of a given domain, which will be
 * compared with the same set of metrics coming from the other versions.
 *
 * @author agazzarini
 * @since 1.0
 */
public class ConfigurationVersion extends DomainMember {
    private List<Metric> metrics = new ArrayList<>();

    @Override
    @JsonIgnore
    public List getChildren() {
        return super.getChildren();
    }

    public void addAll(final List<Metric> data) {
        metrics.addAll(data);
    }

    public Stream<Metric> stream() {
        return metrics.stream();
    }

    public List<Metric> getMetrics() {
        return metrics;
    }
}
