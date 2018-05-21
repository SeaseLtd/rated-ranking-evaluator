package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Object representation of the documents which compose the test collection.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Corpus extends DomainMember<Configuration> {
    /**
     * Builds a new {@link Corpus} instance with the given name or identifier.
     *
     * @param name the entity name or identifier.
     */
    public Corpus(final String name) {
        super(name);
    }

    @JsonProperty("version")
    public List<Configuration> getChildren() {
        return super.getChildren();
    }
}
