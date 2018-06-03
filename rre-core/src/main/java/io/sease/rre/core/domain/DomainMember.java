package io.sease.rre.core.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.impl.AveragedMetric;

import java.math.BigDecimal;
import java.util.*;
import java.util.function.Supplier;

import static java.util.Optional.ofNullable;

/**
 * Supertype layer for all RRE domain entities.
 * It defines the common composite structure shared by all RRE entities.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class DomainMember<C extends DomainMember> {
    @JsonProperty("metrics")
    protected final Map<String, Metric> metrics = new LinkedHashMap<>();
    private final Map<String, C> childrenLookupCache = new HashMap<>();
    private final List<C> children = new ArrayList<>();

    private String name;
    private DomainMember parent;

    /**
     * Adds the given child to this entity.
     *
     * @param child the child entity.
     */
    private C add(final C child) {
        children.add(child);
        return child;
    }

    /**
     * Finds or creates a new child with the given name.
     *
     * @param name the child name (which is used as its identifier).
     * @param factory a supplier that will be used for creating a new instance of requested child (if it doesn't exist).
     * @return a child with the given name.
     */
    @SuppressWarnings("unchecked")
    public C findOrCreate(final String name, final Supplier<C> factory) {
        return childrenLookupCache.computeIfAbsent(name, key -> add((C) factory.get().setName(name).setParent(this)));
    }

    /**
     * Sets the name of this domain entity.
     *
     * @param name the entity name.
     * @return this entity.
     */
    public DomainMember setName(final String name) {
        this.name = name;
        return this;
    }

    /**
     * Sets the parent of this domain entity.
     *
     * @param parent the entity parent.
     * @return this entity.
     */
    private DomainMember setParent(final DomainMember parent) {
        this.parent = parent;
        return this;
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

    /**
     * Collects a leaf metric data (which has been just computed).
     *
     * @param version the version associated with the metric.
     * @param value the metric value.
     * @param name the metric name.
     */
    private void collectLeafMetric(final String version, final BigDecimal value, final String name) {
        metric(name).collect(version, value);
        ofNullable(parent).ifPresent(p -> p.collectLeafMetric(version, value, name));
    }

    /**
     * Returns the {@link AveragedMetric} instance associated with the given name.
     *
     * @param name the metric name.
     * @return the {@link AveragedMetric} instance associated with the given name.
     */
    private AveragedMetric metric(final String name) {
        return (AveragedMetric) metrics.computeIfAbsent(name, k -> new AveragedMetric(name));
    }

    public void notifyCollectedMetrics() {
        metrics.values().stream()
                .flatMap(metric -> metric.getVersions().entrySet().stream())
                .forEach(entry ->
                    ofNullable(parent)
                            .ifPresent(p -> p.collectLeafMetric(
                                    entry.getKey(),
                                    entry.getValue().value(),
                                    entry.getValue().owner().getName())));
    }
}