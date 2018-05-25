package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class QueryGroup extends DomainMember<QueryEvaluation> {
    @Override
    @JsonProperty("query-evaluations")
    public List<QueryEvaluation> getChildren() {
        return super.getChildren();
    }
}