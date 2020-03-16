/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.Func;
import io.sease.rre.core.domain.metrics.HitsCollector;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.MetricClassManagerFactory;

import java.util.*;
import java.util.function.Function;
import java.util.stream.Collector;

import static io.sease.rre.Field.DEFAULT_ID_FIELD_NAME;
import static java.util.Optional.ofNullable;
import static java.util.stream.Collectors.toMap;

/**
 * An evaluation (i.e. a set of measures / metrics) at query-level.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Query extends DomainMember<Query> implements HitsCollector {
    protected String idFieldName = DEFAULT_ID_FIELD_NAME;
    protected JsonNode relevantDocuments;
    protected String searchEngineQueryRequest;
    protected String blackBoxQueryRequest;

    @Override
    public DomainMember setName(final String query) {
        return super.setName(query);
    }

    @JsonProperty("results")
    private Map<String, MutableQueryOrSearchResponse> results = new LinkedHashMap<>();

    @Override
    @JsonProperty("query")
    public String getName() {
        return super.getName();
    }

    /**
     * Populates this query instance with the available metrics.
     * Note that those metrics instances are empty (i.e. no value) at this time. Before getting their values, the
     * search results accumulation phase needs to be executed.
     *
     * @param metrics the metrics instances associated with this instance.
     */
    public void prepare(final List<Metric> metrics) {
        this.metrics.putAll(
                metrics.stream()
                        .map(metric -> new AbstractMap.SimpleEntry<>(metric.getName(), metric))
                        .collect(
                                toLinkedMap(
                                        AbstractMap.SimpleEntry::getKey,
                                        AbstractMap.SimpleEntry::getValue)));
    }

    @Override
    public void setTotalHits(final long totalHits, final String version) {
        metrics.values().forEach(metric -> metric.setTotalHits(totalHits, version));
        results.computeIfAbsent(version, v -> new MutableQueryOrSearchResponse()).setTotalHits(totalHits, version);
    }

    @Override
    public void collect(final Map<String, Object> hit, final int rank, final String version) {
        metrics.values().forEach(metric -> metric.collect(hit, rank, version));

        judgment(id(hit)).ifPresent(jNode -> {
            hit.put("_isRelevant", true);
            hit.put("_gain", Func.gainOrRatingNode(jNode).map(JsonNode::decimalValue)
                    .orElse(MetricClassManagerFactory.getInstance().getDefaultMissingGrade()));
        });

        results.computeIfAbsent(version, v -> new MutableQueryOrSearchResponse()).collect(hit, rank, version);
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

    @Override
    @JsonIgnore
    @SuppressWarnings("unchecked")
    public List getChildren() {
        return super.getChildren();
    }

    @JsonIgnore
    public Map<String, MutableQueryOrSearchResponse> getResults() {
        return results;
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

    private static <T, K, U> Collector<T, ?, Map<K, U>> toLinkedMap(
            Function<? super T, ? extends K> keyMapper,
            Function<? super T, ? extends U> valueMapper) {
        return toMap(
                keyMapper,
                valueMapper,
                (u, v) -> {
                    throw new IllegalStateException(String.format("Duplicate key %s", u));
                },
                LinkedHashMap::new);
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

    public String getSearchEngineQueryRequest() {
        return searchEngineQueryRequest;
    }

    public void setSearchEngineQueryRequest(String searchEngineQueryRequest) {
        this.searchEngineQueryRequest = searchEngineQueryRequest;
    }

    public String getBlackBoxQueryRequest() {
        return blackBoxQueryRequest;
    }

    public void setBlackBoxQueryRequest(String blackBoxQueryRequest) {
        this.blackBoxQueryRequest = blackBoxQueryRequest;
    }
}