package io.sease.rre.core.domain.metrics;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static io.sease.rre.Calculator.subtract;
import static io.sease.rre.Field.DEFAULT_ID_FIELD_NAME;
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
 * A metric doesn't provide directly a value: this because within the RRE data model we can have several versions of
 * the same metric associated to different configurations. Although the metric is always the same, the value can
 * change between version; as consequence of that, the "value" computation itself is delegated to a special class
 * called, not surprisingly, {@link ValueFactory}.
 *
 * @see ValueFactory
 * @author agazzarini
 * @since 1.0
 */
public abstract class Metric implements HitsCollector {
    private final String name;

    protected String idFieldName = DEFAULT_ID_FIELD_NAME;
    protected JsonNode relevantDocuments;
    protected Map<String, ValueFactory> values = new LinkedHashMap<>();

    /**
     * Sets into this metrics the different versions available in the current evaluation process.
     *
     * @param versions the different versions available in the current evaluation process.
     */
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
     * This name defaults to "id", which probably covers the 99% of the scenarios.
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
     * Assuming the metric provides more than one version, this method returns the metric trend in terms of delta
     * between (subsequent) versions.
     *
     * @return the delta between the subsequent versioned values.
     */
    @JsonProperty("trend")
    public List<BigDecimal> trend() {
        if (values.isEmpty()) return emptyList();
        if (values.size() == 1) return singletonList(values.values().iterator().next().value());

        final List<ValueFactory> onlyValueFactories = new ArrayList<>(values.values());
        return range(0, onlyValueFactories.size() - 1)
                .mapToObj(index -> subtract(onlyValueFactories.get(index + 1).value(), onlyValueFactories.get(index).value()))
                .collect(toList());
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

    /**
     * A metric must provide an {@link ValueFactory} instance which will be used for actually computing its value(s).
     *
     * @return the factory which will be used for actually computing metric value(s).
     */
    public abstract ValueFactory valueFactory();

    /**
     * Returns a map of the available versions with the corresponding value factory.
     *
     * @return a map of the available versions with the corresponding value factory.
     */
    public Map<String, ValueFactory> getVersions() {
        return values;
    }

    /**
     * Returns the {@link ValueFactory} instance associated with a given version.
     *
     * @param version the target version.
     * @return the {@link ValueFactory} instance associated with a given version.
     */
    public ValueFactory valueFactory(final String version) {
        return values.getOrDefault(version, valueFactory());
    }
}