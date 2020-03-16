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
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

import static io.sease.rre.Func.gainOrRatingNode;
import static java.math.BigDecimal.ONE;

/**
 * ERR metric.
 *
 * @author binarymax
 * @since 1.0
 */
public class ExpectedReciprocalRank extends Metric {

    private final BigDecimal fairgrade;
    private final BigDecimal maxgrade;
    private final int k;

    private final static BigDecimal TWO = new BigDecimal(2);

    /**
     * Builds a new ExpectedReciprocalRank metric with the default gain unit function and one diversity topic.
     *
     * @param k            the top k reference elements used for building the measure.
     * @param maxgrade     the maximum grade available when judging documents. If
     *                     {@code null}, will default to {@link Metric#DEFAULT_MAX_GRADE}.
     * @param defaultgrade the default grade to use when judging documents. If
     *                     {@code null}, will default to either {@code maxgrade / 2}
     *                     or {@link Metric#DEFAULT_MISSING_GRADE}, depending
     *                     whether or not {@code maxgrade} has been specified.
     */
    public ExpectedReciprocalRank(@JsonProperty("maxgrade") final Float maxgrade,
                                  @JsonProperty("defaultgrade") final Float defaultgrade,
                                  @JsonProperty("k") final int k) {
        super("ERR" + "@" + k);
        if (maxgrade == null) {
            this.maxgrade = DEFAULT_MAX_GRADE;
            this.fairgrade = Optional.ofNullable(defaultgrade).map(BigDecimal::valueOf).orElse(DEFAULT_MISSING_GRADE);
        } else {
            this.maxgrade = BigDecimal.valueOf(maxgrade);
            this.fairgrade = Optional.ofNullable(defaultgrade).map(BigDecimal::valueOf).orElseGet(() -> this.maxgrade.divide(TWO, 8, RoundingMode.HALF_UP));
        }
        this.k = k;
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            private BigDecimal ERR = BigDecimal.ZERO;
            private BigDecimal trust = ONE;
            private BigDecimal value = fairgrade;
            private int totalHits = 0;
            private int totalDocs = 0;

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                if (++totalDocs > k) return;
                value = fairgrade;
                judgment(id(hit))
                        .ifPresent(judgment -> {
                            value = gainOrRatingNode(judgment).map(JsonNode::decimalValue).orElse(fairgrade);
                            totalHits++;
                        });
                BigDecimal r = BigDecimal.valueOf(rank);
                BigDecimal usefulness = gain(value, maxgrade);
                BigDecimal discounted = usefulness.divide(r, 8, RoundingMode.HALF_UP);
                ERR = ERR.add(trust.multiply(discounted));
                trust = trust.multiply(ONE.subtract(usefulness));
            }

            @Override
            public BigDecimal value() {
                if (totalHits == 0) {
                    return (totalDocs == 0) ? ONE : BigDecimal.ZERO;
                }
                return ERR;
            }
        };
    }

    private BigDecimal gain(BigDecimal grade, BigDecimal max) {
        // Need to use Math.pow() here - BigDecimal.pow() is integer-only
        final BigDecimal numer = BigDecimal.valueOf(Math.pow(TWO.doubleValue(), grade.doubleValue())).subtract(ONE);
        final BigDecimal denom = BigDecimal.valueOf(Math.pow(TWO.doubleValue(), max.doubleValue()));
        if (denom.equals(BigDecimal.ZERO)) {
            return BigDecimal.ZERO;
        }
        return numer.divide(denom, 8, RoundingMode.HALF_UP);
    }

    @Override
    public int getRequiredResults() {
        return k;
    }
}
