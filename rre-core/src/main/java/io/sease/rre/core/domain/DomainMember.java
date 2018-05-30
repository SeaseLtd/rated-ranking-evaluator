package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.domain.metrics.CompoundMetric;
import io.sease.rre.core.event.MetricEvent;
import io.sease.rre.core.event.MetricEventListener;

import java.util.*;
import java.util.function.Supplier;
import java.util.stream.Stream;

import static java.util.Optional.ofNullable;
import static java.util.stream.Collectors.toList;

/**
 * Supertype layer for all RRE domain entities.
 * It defines the common composite structure shared by all RRE entities.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class DomainMember<C extends DomainMember> implements MetricEventListener {
    private String name;

    private Map<String, C> childrenLookupCache = new HashMap<>();
    protected Map<String, List<CompoundMetric>> compoundMetrics = new LinkedHashMap<>();

    protected List<Class<? extends CompoundMetric>> compoundMetricsDef;

    private List<C> children = new ArrayList<>();

    /**
     * Adds the given child to this entity.
     *
     * @param child the child entity.
     */
    public C add(final C child) {
        children.add(child);
        return child;
    }

    public <T extends DomainMember> T init(final List<Class<? extends CompoundMetric>> metricsDef) {
        this.compoundMetricsDef = metricsDef;
        return (T) this;
    }

    @Override
    public void newMetricHasBeenComputed(final MetricEvent event) {
        compoundMetrics.computeIfAbsent(event.getVersion(), v -> newCompoundMetricSet())
            .forEach(compoundMetric -> compoundMetric.collect(event.getMetric()));
    }

    private List<CompoundMetric> newCompoundMetricSet() {
        return compoundMetricsDef
                .stream()
                .map(clazz -> {
                    try {
                        return clazz.newInstance();
                    } catch (final Exception exception) {
                        exception.printStackTrace();
                        return null;
                    }})
                .filter(Objects::nonNull)
                .collect(toList());
    }

    public C findOrCreate(final String name, final Supplier<C> factory) {
        return childrenLookupCache.computeIfAbsent(name, key -> add((C) factory.get().setName(name)));
    }

    public DomainMember setName(final String name) {
        this.name = name;
        return this;
    }

    @JsonProperty("compound-metrics")
    public Map<String, List<CompoundMetric>> getCompoundMetrics() {
        return compoundMetrics;
    }

    /**
     * Returns the children stream.
     *
     * @return the children stream.
     */
    public Stream<C> childrenStream() {
        return children.stream();
    }

    /**
     * Returns the children of this entity.
     *
     * @return the children of this entity.
     */
    public List<C> getChildren() {
        return children;
    }

    /**
     * Returns the name of this entity.
     *
     * @return the name of this entity.
     */
    public String getName() {
        return name;
    }
}