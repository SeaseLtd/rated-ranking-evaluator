package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * A group of queries which are supposed to produce the same exact results.
 *
 * @author agazzarini
 * @since 1.0
 */
public class QueryGroup extends DomainMember<QueryEvaluation> {
    @Override
    @JsonProperty("query-evaluations")
    public List<QueryEvaluation> getChildren() {
        return super.getChildren();
    }
}