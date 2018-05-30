package io.sease.rre.core.event;

public interface MetricEventListener {
    void newMetricHasBeenComputed(MetricEvent event);
}
