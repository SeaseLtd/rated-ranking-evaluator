package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * A configuration version.
 * Each version is supposed to be a configuration "instance" of a given domain, which will be
 * compared with the same set of metrics coming from the other versions.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Configuration extends DomainMember<Topic> {
    /**
     * Builds a new {@link Configuration} instance with the given name or identifier.
     *
     * @param name the entity name or identifier.
     */
    public Configuration(final String name) {
        super(name);
    }

    @JsonProperty("topics")
    public List<Topic> getChildren() {
        return super.getChildren();
    }
}
