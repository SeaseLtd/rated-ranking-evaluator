package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.domain.metrics.CompoundMetric;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.event.MetricEvent;
import io.sease.rre.core.event.MetricEventListener;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static java.util.Optional.ofNullable;

/**
 * A group of queries which are supposed to produce the same exact results.
 *
 * @author agazzarini
 * @since 1.0
 */
public class QueryGroup extends DomainMember<QueryEvaluation> implements MetricEventListener {
    @Override
    @JsonProperty("query-evaluations")
    public List<QueryEvaluation> getChildren() {
        return super.getChildren();
    }
}