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
    /**
     * Builds a new {@link Topic} instance with the given name or identifier.
     *
     * @param name the topic name or identifier.
     */
    public Topic(final String name) {
        super(name);
    }

    @JsonProperty("query-groups")
    public List<QueryGroup> getChildren() {
        return super.getChildren();
    }
}
