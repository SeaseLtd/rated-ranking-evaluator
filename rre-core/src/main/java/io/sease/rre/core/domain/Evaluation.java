package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.EventCollector;

import java.util.List;

/**
 * The evaluation result.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Evaluation extends DomainMember<Corpus> implements EventCollector<QueryEvaluation> {
    @JsonProperty("corpora")
    public List<Corpus> getChildren() {
        return super.getChildren();
    }

    @Override
    public void collect(final QueryEvaluation event) {
        // TODO
    }
}