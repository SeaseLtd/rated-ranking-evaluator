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
package io.sease.rre.core.domain.metrics;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.databind.JsonNode;

import java.math.BigDecimal;
import java.util.Map;
import java.util.Optional;

import static java.util.Optional.ofNullable;

/**
 * A metric valueFactory.
 * The metric valueFactory has been decoupled from the metric itself because RRE domain model introduces a "versioning" in
 * values. So actually this is a "versioned" valueFactory of a given metric, where "versioned" means it has been computed
 * using a given configuration version.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class ValueFactory implements HitsCollector {
    private final String version;
    private final Metric owner;
    protected long totalHits;

    /**
     * Builds a new (Metric) valueFactory with the given (metric) owner.
     *
     * @param owner the owner metric.
     */
    protected ValueFactory(final Metric owner, final String version){
        this.owner = owner;
        this.version = version;
    }

    public Metric owner() {
        return owner;
    }

    @Override
    public void setTotalHits(final long totalHits, final String version) {
        this.totalHits = totalHits;
    }

    /**
     * Returns the valueFactory of this metric.
     *
     * @return the valueFactory of this metric.
     */
    public abstract BigDecimal value();

    /**
     * Returns the judgment associated with the given identifier.
     *
     * @param id the document identifier.
     * @return an optional describing the judgment associated with the given identifier.
     */
    protected Optional<JsonNode> judgment(final String id) {
        return ofNullable(owner.relevantDocuments).map(judgements -> judgements.get(id));
    }

    /**
     * Extracts the id field valueFactory from the given document.
     *
     * @param document the document (i.e. a search hit).
     * @return the id field valueFactory of the input document.
     */
    protected String id(final Map<String, Object> document) {
        return String.valueOf(document.get(owner.idFieldName));
    }

    /**
     * Returns the valueFactory of this metric (as a string).
     * Note that the goal of this method is the same as {@link #value()}. As you can see
     * the difference is in the result kind (a string instead of a number) and it is mainly
     * used for JSON serialization purposes.
     *
     * @return the valueFactory of this metric (as a string).
     */
    public String getValue() {
        return value().toPlainString();
    }

    @JsonIgnore
    public long getTotalHits() {
        return totalHits;
    }

    @Override
    public String toString() {
        return owner.getName() +
                "(" + ofNullable(version).orElse("N.A.") + ") = " +
                getValue();
    }
}