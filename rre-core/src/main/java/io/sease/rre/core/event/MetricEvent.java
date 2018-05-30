package io.sease.rre.core.event;

import io.sease.rre.core.domain.metrics.Metric;

import java.util.EventObject;

public final class MetricEvent extends EventObject {
    private final Metric metric;
    private final String version;

    /**
     * Constructs new metric event.
     *
     * @param source The object on which the Event initially occurred.
     * @throws IllegalArgumentException if source is null.
     */
    public MetricEvent(final Metric metric, final String version, final Object source) {
        super(source);
        this.metric = metric;
        this.version = version;
    }

    public Metric getMetric() {
        return metric;
    }

    public String getVersion() {
        return version;
    }
}
