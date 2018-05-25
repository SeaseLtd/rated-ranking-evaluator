package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.EventCollector;

import java.text.DateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

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

    public Evaluation() {
        setName("Ranking Evaluation Report - created on " + DateFormat.getDateInstance(DateFormat.FULL, Locale.ENGLISH).format(new Date()));
    }

    @Override
    public void collect(final QueryEvaluation event) {
        // TODO
    }
}