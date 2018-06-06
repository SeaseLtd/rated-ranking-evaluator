package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.domain.metrics.HitsCollector;
import io.sease.rre.core.domain.metrics.Metric;

import java.util.AbstractMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collector;
import java.util.stream.Collectors;

import static java.util.stream.Collectors.toMap;

/**
 * An evaluation (i.e. a set of measures / metrics) at query-level.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Query extends DomainMember<Query> implements HitsCollector {
    @Override
    public DomainMember setName(final String query) {
        return super.setName(query);
    }

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
    }

    @Override
    public void collect(final Map<String, Object> hit, final int rank, final String version) {
        metrics.values().forEach(metric -> metric.collect(hit, rank, version));
    }

    @Override
    @JsonIgnore
    @SuppressWarnings("unchecked")
    public List getChildren() {
        return super.getChildren();
    }

    public static <T, K, U> Collector<T, ?, Map<K,U>> toLinkedMap(
            Function<? super T, ? extends K> keyMapper,
            Function<? super T, ? extends U> valueMapper)  {
        return toMap(
                keyMapper,
                valueMapper,
                (u, v) -> { throw new IllegalStateException(String.format("Duplicate key %s", u)); },
                LinkedHashMap::new);
    }
}