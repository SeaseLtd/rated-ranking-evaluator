package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Object representation of the documents which compose the test collection.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Corpus extends DomainMember<Topic> {
    @JsonProperty("topics")
    public List<Topic> getChildren() {
        return super.getChildren();
    }
}
