package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * A group of queries (actually query variants) which are supposed to produce the same exact results.
 *
 * @author agazzarini
 * @since 1.0
 */
public class QueryGroup extends DomainMember<Query> {
    @Override
    @JsonProperty("query-evaluations")
    public List<Query> getChildren() {
        return super.getChildren();
    }
}