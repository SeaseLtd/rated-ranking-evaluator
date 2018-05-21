package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * The evaluation result.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Evaluation extends DomainMember<Corpus> {
    /**
     * Builds a new {@link Evaluation} instance.
     */
    public Evaluation() {
        super("evaluation");
    }

    @JsonProperty("corpora")
    public List<Corpus> getChildren() {
        return super.getChildren();
    }
}