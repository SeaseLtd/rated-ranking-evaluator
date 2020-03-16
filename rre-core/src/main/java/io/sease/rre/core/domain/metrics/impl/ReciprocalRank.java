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
package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.Func;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.MetricClassManagerFactory;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * The reciprocal rank of a query response is the multiplicative inverse of the rank of the first correct answer.
 *
 * @author agazzarini
 * @since 1.0
 */
public class ReciprocalRank extends Metric {

    private final int k;
    private final BigDecimal maxgrade;
    private final BigDecimal fairgrade;

    /**
     * Builds a new ReciprocalRank at 10 metric.
     */
    public ReciprocalRank() {
        this(10, null, null);
    }

    /**
     * Builds a new Reciprocal Rank at K metric.
     *
     * @param k the top k reference elements used for building the measure.
     * @param maxgrade     the maximum grade available when judging documents. If
     *                     {@code null}, will default to 3.
     * @param defaultgrade the default grade to use when judging documents. If
     *                     {@code null}, will default to either {@code maxgrade / 2}
     *                     or 2, depending whether or not {@code maxgrade} has been specified.
     */
    public ReciprocalRank(@JsonProperty("k") final int k,
                          @JsonProperty("maxgrade") final Float maxgrade,
                          @JsonProperty("defaultgrade") final Float defaultgrade) {
        super("RR@" + k);
        this.k = k;
        if (maxgrade == null) {
            this.maxgrade = MetricClassManagerFactory.getInstance().getDefaultMaximumGrade();
            this.fairgrade = Optional.ofNullable(defaultgrade).map(BigDecimal::valueOf).orElse(MetricClassManagerFactory.getInstance().getDefaultMissingGrade());
        } else {
            this.maxgrade = BigDecimal.valueOf(maxgrade);
            this.fairgrade = Optional.ofNullable(defaultgrade).map(BigDecimal::valueOf).orElseGet(() -> this.maxgrade.divide(BigDecimal.valueOf(2), 8, RoundingMode.HALF_UP));
        }
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            private int rank;
            private BigDecimal maxGain = BigDecimal.ZERO;
            private int totalDocs = 0;

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                if (++totalDocs > k) return;
                judgment(id(hit))
                        .ifPresent(hitData -> {
                            final BigDecimal gain = Func.gainOrRatingNode(hitData).map(JsonNode::decimalValue).orElse(fairgrade);
                            if (gain.compareTo(maxGain) > 0) {
                                this.rank = rank;
                                this.maxGain = gain;
                            }
                        });
            }

            @Override
            public BigDecimal value() {
                if (relevantDocuments.size() == 0) {
                    return totalHits == 0 ? BigDecimal.ONE : BigDecimal.ZERO;
                }
                if (rank == 0) {
                    return BigDecimal.ZERO;
                }

                return BigDecimal.ONE.divide(new BigDecimal(rank), 2, RoundingMode.HALF_UP);
            }
        };
    }
}