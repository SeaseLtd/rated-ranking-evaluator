package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * An evaluation (i.e. a set of measures / metrics) at query-level.
 *
 * @author agazzarini
 * @since 1.0
 */
public class QueryEvaluation extends DomainMember<ConfigurationVersion> {

    @Override
    public DomainMember setName(final String query) {
        return super.setName(query);
    }

    @Override
    @JsonProperty("query")
    public String getName() {
        return super.getName();
    }

    @Override
    @JsonProperty("versions")
    public List<ConfigurationVersion> getChildren() {
        return super.getChildren();
    }
}
