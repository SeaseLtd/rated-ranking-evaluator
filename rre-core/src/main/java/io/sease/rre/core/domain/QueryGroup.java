package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class QueryGroup extends DomainMember<QueryEvaluation> {
    private String description;

    /**
     * Builds a new {@link QueryGroup} instance with the given name or identifier.
     *
     * @param name the entity name or identifier.
     * @param description the entity description.
     */
    public QueryGroup(final String name, final String description) {
        super(name);
        this.description = description;
    }

    @JsonProperty("query-evaluations")
    public List<QueryEvaluation> getChildren() {
        return super.getChildren();
    }

    /**
     * Returns the description of this query group.
     *
     * @return the description of this query group.
     */
    public String getDescription() {
        return description;
    }
}