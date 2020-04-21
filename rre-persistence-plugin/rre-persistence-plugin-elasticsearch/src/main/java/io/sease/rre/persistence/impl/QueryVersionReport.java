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
package io.sease.rre.persistence.impl;

import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import io.sease.rre.core.domain.*;
import io.sease.rre.core.domain.metrics.MetricUtils;
import org.apache.commons.codec.digest.DigestUtils;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

import static java.util.Optional.ofNullable;

/**
 * Single query item that can be imported to Elasticsearch or a similar
 * persistence endpoint.
 * <p>
 * Each item represents a single version of a query, including the metrics
 * generated for that version. Metric names will be sanitised.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
@JsonInclude(JsonInclude.Include.NON_EMPTY)
public class QueryVersionReport {

    private final String id;
    private final String corpora;
    private final String topic;
    private final String queryGroup;
    private final String queryText;
    private final String version;
    private final long totalHits;
    private final Collection<VersionMetric> metrics;
    private final Map<String, BigDecimal> metricValues;
    private final Collection<Result> results;

    public QueryVersionReport(String id, String corpora, String topic, String queryGroup, String queryText,
                              String version, long totalHits, Collection<VersionMetric> metrics,
                              Collection<Result> results) {
        this.id = id;
        this.corpora = corpora;
        this.topic = topic;
        this.queryGroup = queryGroup;
        this.queryText = queryText;
        this.version = version;
        this.totalHits = totalHits;
        this.metrics = metrics;
        this.metricValues = metrics.stream()
                .collect(Collectors.toMap(VersionMetric::getSanitisedName, VersionMetric::getValue));
        this.results = results;
    }

    /**
     * Convert a {@link Query} object into one or more QueryVersionReport
     * items.
     * <p>
     * This will build one QueryVersionReport per version found in the
     * incoming query's metrics, effectively flattening the query.
     *
     * @param query the query to be converted.
     * @return a list of query versions, including metrics.
     */
    public static List<QueryVersionReport> fromQuery(final Query query) {
        // Get the fixed metadata
        final String corpus = findParentName(query, Corpus.class);
        final String topic = findParentName(query, Topic.class);
        final String queryGroup = findParentName(query, QueryGroup.class);
        final String queryText = query.getName();

        // Extract the metrics first
        Map<String, Map<String, VersionMetric>> versionMetrics = new HashMap<>();
        Map<String, Long> versionHits = new HashMap<>();
        query.getMetrics().values().forEach(m -> {
            final String metricName = m.getName();
            final String sanitised = MetricUtils.sanitiseName(m);
            m.getVersions().forEach((version, valueFactory) -> {
                versionMetrics.putIfAbsent(version, new HashMap<>());
                versionMetrics.get(version).put(sanitised, new VersionMetric(metricName, sanitised, valueFactory.value()));
                versionHits.putIfAbsent(version, valueFactory.getTotalHits());
            });
        });

        // Extract the results
        Map<String, Collection<Result>> results = extractResults(query);

        // Convert to a list of QueryVersionReport items, and return
        return versionMetrics.keySet().stream()
                .map(v -> new QueryVersionReport(
                        createId(corpus, topic, queryGroup, query.getName(), v),
                        corpus, topic, queryGroup, queryText, v, versionHits.get(v),
                        versionMetrics.get(v).values(), results.get(v)))
                .collect(Collectors.toList());
    }

    private static Map<String, Collection<Result>> extractResults(Query query) {
        Map<String, Collection<Result>> results = new HashMap<>();
        query.getResults().forEach((v, rs) -> {
            Collection<Result> hits = rs.hits().stream()
                    .map(Result::new)
                    .collect(Collectors.toList());
            results.put(v, hits);
        });
        return results;
    }

    private static String createId(String corpus, String topic, String queryGroup, String queryText, String version) {
        final StringBuilder builder = new StringBuilder(ofNullable(corpus).orElse("corpus"));
        for (String s : new String[]{topic, queryGroup, queryText, version}) {
            builder.append("_").append(ofNullable(s).orElse(""));
        }
        return DigestUtils.md5Hex(builder.toString());
    }

    private static String findParentName(Query query, Class<? extends DomainMember> parentClass) {
        String ret = null;

        DomainMember<?> current = query;
        while (current.getParent().isPresent()) {
            current = current.getParent().get();
            if (current.getClass().equals(parentClass)) {
                ret = current.getName();
            }
        }

        return ret;
    }


    public String getId() {
        return id;
    }

    public String getCorpora() {
        return corpora;
    }

    public String getTopic() {
        return topic;
    }

    public String getQueryGroup() {
        return queryGroup;
    }

    public String getQueryText() {
        return queryText;
    }

    public String getVersion() {
        return version;
    }

    public long getTotalHits() {
        return totalHits;
    }

    public Collection<VersionMetric> getMetrics() {
        return metrics;
    }

    public Map<String, BigDecimal> getMetricValues() {
        return metricValues;
    }

    public Collection<Result> getResults() {
        return results;
    }

    public static class VersionMetric {

        private final String name;
        private final String sanitisedName;
        private final BigDecimal value;

        public VersionMetric(String name, String sanitisedName, BigDecimal value) {
            this.name = name;
            this.sanitisedName = sanitisedName;
            this.value = value;
        }

        public String getName() {
            return name;
        }

        public String getSanitisedName() {
            return sanitisedName;
        }

        public BigDecimal getValue() {
            return value;
        }
    }

    public static class Result {

        private final Map<String, Object> content = new HashMap<>();

        public Result(Map<String, Object> resultContent) {
            this.content.putAll(resultContent);
        }

        @JsonAnyGetter
        public Map<String, Object> getContent() {
            return content;
        }

        @JsonAnySetter
        public void setContent(String field, Object value) {
            content.put(field, value);
        }
    }
}
