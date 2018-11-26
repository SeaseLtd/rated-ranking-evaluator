package io.sease.rre.persistence.impl;

import com.fasterxml.jackson.annotation.JsonAnyGetter;
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

    public QueryVersionReport(String id, String corpora, String topic, String queryGroup, String queryText,
                              String version, long totalHits, Collection<VersionMetric> metrics) {
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
        // Extract the metrics first
        Map<String, Map<String, VersionMetric>> versionMetrics = new HashMap<>();
        Map<String, Long> versionHits = new HashMap<>();
        query.getMetrics().values().forEach(m -> {
            final String metricName = m.getName();
            final String sanitised = MetricUtils.sanitiseName(m);
            m.getVersions().forEach((version, valueFactory) -> {
                if (!versionMetrics.containsKey(version)) {
                    versionMetrics.put(version, new HashMap<>());
                }
                versionMetrics.get(version).put(sanitised, new VersionMetric(metricName, sanitised, valueFactory.value()));
                versionHits.putIfAbsent(version, valueFactory.getTotalHits());
            });
        });

        // Get the fixed metadata
        final String corpora = findParentName(query, Corpus.class);
        final String topic = findParentName(query, Topic.class);
        final String queryGroup = findParentName(query, QueryGroup.class);
        final String queryText = query.getName();

        // Convert to a list of QueryVersionReport items, and return
        return versionMetrics.keySet().stream()
                .map(v -> new QueryVersionReport(
                        createId(topic, queryGroup, query.getName(), v),
                        corpora, topic, queryGroup, queryText, v, versionHits.get(v),
                        versionMetrics.get(v).values()))
                .collect(Collectors.toList());
    }

    private static String createId(String topic, String queryGroup, String queryText, String version) {
        final StringBuilder builder = new StringBuilder(ofNullable(topic).orElse("topic"));
        for (String s : new String[]{queryGroup, queryText, version}) {
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

    /**
     * Get the map of sanitised metric name to its value, so these
     * can be stored at the top level and queried without using nested
     * fields.
     *
     * @return the metric value map.
     */
    @JsonAnyGetter
    public Map<String, BigDecimal> getMetricValues() {
        return metricValues;
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

}
