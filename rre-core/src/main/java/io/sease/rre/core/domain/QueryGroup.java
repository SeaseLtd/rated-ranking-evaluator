package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.event.MetricEventListener;

import java.util.List;

/**
 * A group of queries which are supposed to produce the same exact results.
 *
 * @author agazzarini
 * @since 1.0
 */
public class QueryGroup extends DomainMember<Query> implements MetricEventListener {
    @Override
    @JsonProperty("query-evaluations")
    public List<Query> getChildren() {
        return super.getChildren();
    }
}