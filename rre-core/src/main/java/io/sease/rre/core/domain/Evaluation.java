package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;

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
public class Evaluation extends DomainMember<Corpus> {
    @JsonProperty("corpora")
    public List<Corpus> getChildren() {
        return super.getChildren();
    }

    /**
     * Builds a new {@link Evaluation} instance.
     */
    public Evaluation() {
        setName("Ranking Evaluation Report - created on " + DateFormat.getDateInstance(DateFormat.FULL, Locale.ENGLISH).format(new Date()));
    }
}