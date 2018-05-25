package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * A topic represents in this context an information need,
 * a subject (with a given level of granularity) which defines a user's search intent.
 *
 * @author agazzarini
 * @since 1.0
 * @see <a href="https://en.wikipedia.org/wiki/Information_needs">Information Need (Wikipedia)</a>
 */
public class Topic extends DomainMember<QueryGroup> {
    @JsonProperty("query-groups")
    public List<QueryGroup> getChildren() {
        return super.getChildren();
    }
}
