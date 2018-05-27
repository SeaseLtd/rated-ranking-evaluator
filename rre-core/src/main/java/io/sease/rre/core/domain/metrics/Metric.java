package io.sease.rre.core.domain.metrics;

import com.fasterxml.jackson.databind.JsonNode;

import java.math.BigDecimal;
import java.util.Map;
import java.util.Optional;

import static java.util.Optional.ofNullable;

/**
 * Supertype layer for all evaluation metrics.
 * An evaluation metric, within an information retrieval system context,
 * is used to assess how well the search results satisfied the user's query intent.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class Metric implements HitsCollector {
    private final String name;

    private String idFieldName = "id";
    protected JsonNode relevantDocuments;
    protected long totalHits;

    /**
     * Builds a new {@link Metric} with the given mnemonic name.
     *
     * @param name the metric name.
     */
    protected Metric(final String name) {
        this.name = name;
    }

    /**
     * Sets the name of the field which represent the unique key.
     *
     * @param idFieldName the name of the field which represent the unique key.
     */
    public void setIdFieldName(final String idFieldName) {
        this.idFieldName = idFieldName;
    }

    /**
     * Sets the relevant documents / judgments for this metric.
     *
     * @param relevantDocuments the relevant documents / judgments for this metric.
     */
    public void setRelevantDocuments(final JsonNode relevantDocuments) {
        this.relevantDocuments = relevantDocuments;
    }

    /**
     * Sets the total hits (i.e. the total number of results) of the query response associated with this metric.
     *
     * @param totalHits the total hits of the query response associated with this metric.
     */
    public void setTotalHits(final long totalHits) {
        this.totalHits = totalHits;
    }

    /**
     * Returns the value of this metric.
     *
     * @return the value of this metric.
     */
    public abstract BigDecimal value();

    /**
     * Returns the judgment associated with the given identifier.
     *
     * @param id the document identifier.
     * @return an optional describing the judgment associated with the given identifier. 
     */
    public Optional<JsonNode> judgment(final String id) {
        return ofNullable(relevantDocuments).map(judgements -> judgements.get(id));
    }

    /**
     * Extracts the id field value from the given document.
     *
     * @param document the document (i.e. a search hit).
     * @return the id field value of the input document.
     */
    protected String id(final Map<String, Object> document) {
        return String.valueOf(document.get(idFieldName));
    }

    /**
     * Returns the name of this metric.
     *
     * @return the name of this metric.
     */
    public String getName() {
        return name;
    }

    /**
     * Returns the value of this metric (as a string).
     * Note that the goal of this method is the same as {@link #value()}. As you can see
     * the difference is in the result kind (a string instead of a number) and it is mainly
     * used for JSON serialization purposes.
     *
     * @return the value of this metric (as a string).
     */
    public String getValue() {
        return value().toPlainString();
    }

    @Override
    public String toString() {
        return getName() + " = " + getValue();
    }
}