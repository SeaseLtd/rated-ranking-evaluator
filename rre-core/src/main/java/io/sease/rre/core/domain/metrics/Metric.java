package io.sease.rre.core.domain.metrics;

import com.fasterxml.jackson.databind.JsonNode;

import java.math.BigDecimal;
import java.util.*;

import static io.sease.rre.Calculator.subtract;
import static java.util.Collections.emptyList;
import static java.util.Collections.singletonList;
import static java.util.Optional.ofNullable;
import static java.util.stream.Collectors.toList;
import static java.util.stream.IntStream.range;

/**
 * Supertype layer for all metrics.
 * An evaluation metric, within an information retrieval system context,
 * is used to assess how well the search results satisfied the user's query intent.
 *
 * @see Value
 * @author agazzarini
 * @since 1.0
 */
public abstract class Metric implements HitsCollector {
    private final String name;

    protected String idFieldName = "id";
    protected JsonNode relevantDocuments;

    protected Map<String, Value> values = new LinkedHashMap<>();

    public void setVersions(final List<String> versions) {
        versions.forEach(version -> values.put(version, valueFactory()));
    }

    /**
     * Builds a new {@link Metric} with the given mnemonic name.
     *
     * @param name the metric name.
     */
    public Metric(final String name) {
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

    @Override
    public void setTotalHits(final long totalHits, final String version) {
        ofNullable(values.get(version)).ifPresent(value -> value.setTotalHits(totalHits, version));
    }

    @Override
    public void collect(Map<String, Object> hit, int rank, final String version) {
        ofNullable(values.get(version)).ifPresent(value -> value.collect(hit, rank, version));
    }

    /**
     * Assuming the metric provides more than one version, this method returns the metric trend in terms of delta.
     *
     * @return the delta between the subsequent versioned values.
     */
    public List<BigDecimal> trend() {
        if (values.isEmpty()) return emptyList();
        if (values.size() == 1) return singletonList(values.values().iterator().next().value());

        final List<Value> onlyValues = new ArrayList<>(values.values());
        return range(0, onlyValues.size() - 1)
                .mapToObj(index -> subtract(onlyValues.get(index + 1).value(), onlyValues.get(index).value()))
                .collect(toList());
    }

    /**
     * Returns the judgment associated with the given identifier.
     *
     * @param id the document identifier.
     * @return an optional describing the judgment associated with the given identifier. 
     */
    protected Optional<JsonNode> judgment(final String id) {
        return ofNullable(relevantDocuments).map(judgements -> judgements.get(id));
    }

    /**
     * Extracts the id field valueFactory from the given document.
     *
     * @param document the document (i.e. a search hit).
     * @return the id field valueFactory of the input document.
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

    public abstract Value valueFactory();

    public Map<String, Value> getValues() {
        return values;
    }
}