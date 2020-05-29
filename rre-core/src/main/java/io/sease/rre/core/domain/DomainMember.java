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
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.impl.AveragedMetric;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
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
     * @param name    the child name (which is used as its identifier).
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
     * @param value   the metric value.
     * @param name    the metric name.
     */
    private void collectLeafMetric(final String version, final BigDecimal value, final String name) {
        metric(name).collect(version, value);
        ofNullable(parent).ifPresent(p -> p.collectLeafMetric(version, value, name));
    }

    private void initialiseVersions(final String name, final List<String> versions) {
        if (!metrics.containsKey(name)) {
            metric(name).setVersions(versions);
        }
        ofNullable(parent).ifPresent(p -> p.initialiseVersions(name, versions));
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
        // Make sure all of the versions are set at all levels for each metric
        metrics.values()
                .forEach(metric -> initialiseVersions(metric.getName(), new ArrayList<>(metric.getVersions().keySet())));
        metrics.values().stream()
                .flatMap(metric -> metric.getVersions().entrySet().stream())
                .forEach(entry ->
                        ofNullable(parent)
                                .ifPresent(p -> p.collectLeafMetric(
                                        entry.getKey(),
                                        entry.getValue().value(),
                                        entry.getValue().owner().getName())));
    }

    public Map<String, Metric> getMetrics() {
        return metrics;
    }

    @JsonIgnore
    public Optional<DomainMember> getParent() {
        return ofNullable(parent);
    }
}