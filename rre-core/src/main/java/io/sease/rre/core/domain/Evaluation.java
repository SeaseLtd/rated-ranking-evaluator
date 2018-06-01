package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.EventCollector;
import io.sease.rre.core.domain.metrics.CompoundMetric;

import java.text.DateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * The evaluation result.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Evaluation extends DomainMember<Corpus> implements EventCollector<Query> {
    @JsonProperty("corpora")
    public List<Corpus> getChildren() {
        return super.getChildren();
    }

    public Evaluation() {
        setName("Ranking Evaluation Report - created on " + DateFormat.getDateInstance(DateFormat.FULL, Locale.ENGLISH).format(new Date()));
    }

    @Override
    @JsonIgnore
    public Map<String, List<CompoundMetric>> getCompoundMetrics() {
        return super.getCompoundMetrics();
    }

    @Override
    public void collect(final Query event) {
        // TODO
    }
}