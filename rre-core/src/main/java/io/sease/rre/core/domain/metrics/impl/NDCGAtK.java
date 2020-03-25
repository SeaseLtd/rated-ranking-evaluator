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
import io.sease.rre.core.domain.metrics.MetricClassConfigurationManager;
import io.sease.rre.core.domain.metrics.ParameterizedMetricClassManager;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.StreamSupport;

import static io.sease.rre.Func.gainOrRatingNode;
import static java.util.stream.Collectors.groupingBy;

/**
 * NDCG@k metric.
 *
 * @author agazzarini
 * @since 1.0
 */
public class NDCGAtK extends Metric {
    private final static BigDecimal TWO = new BigDecimal(2);

    private final BigDecimal fairgrade;
    private final BigDecimal maxgrade;
    private final int k;

    /**
     * Builds a new NDCGAtK metric with default maximum and missing judgement
     * grades.
     *
     * @param k the top k reference elements used for building the measure.
     */
    public NDCGAtK(final int k) {
        this(k, null, null, null);
    }

    /**
     * Builds a new NDCGAtK metric.
     *
     * @param k the top k reference elements used for building the measure.
     * @param maxgrade     the maximum grade available when judging documents. If
     *                     {@code null}, will default to 3.
     * @param defaultgrade the default grade to use when judging documents. If
     *                     {@code null}, will default to either {@code maxgrade / 2}
     *                     or 2, depending whether or not {@code maxgrade} has been specified.
     * @param name         the name to use for this metric. If {@code null}, will default to {@code NDCG@k}.
     */
    public NDCGAtK(@JsonProperty("k") final int k,
                   @JsonProperty(ParameterizedMetricClassManager.MAXIMUM_GRADE_KEY) final Float maxgrade,
                   @JsonProperty(ParameterizedMetricClassManager.MISSING_GRADE_KEY) final Float defaultgrade,
                   @JsonProperty(ParameterizedMetricClassManager.NAME_KEY) final String name) {
        super(Optional.ofNullable(name).orElse("NDCG@" + k));
        if (maxgrade == null) {
            this.maxgrade = MetricClassConfigurationManager.getInstance().getDefaultMaximumGrade();
            this.fairgrade = Optional.ofNullable(defaultgrade).map(BigDecimal::valueOf).orElse(MetricClassConfigurationManager.getInstance().getDefaultMissingGrade());
        } else {
            this.maxgrade = BigDecimal.valueOf(maxgrade);
            this.fairgrade = Optional.ofNullable(defaultgrade).map(BigDecimal::valueOf).orElseGet(() -> this.maxgrade.divide(TWO, 8, RoundingMode.HALF_UP));
        }
        this.k = k;
    }

    @Override
    public int getRequiredResults() {
        return k;
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            private BigDecimal dcg = BigDecimal.ZERO;

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                if (rank > k) return;
                judgment(id(hit))
                        .ifPresent(judgment -> {
                            final BigDecimal value = gainOrRatingNode(judgment).map(JsonNode::decimalValue).orElse(fairgrade);
                            BigDecimal numerator = BigDecimal.valueOf(Math.pow(TWO.doubleValue(), value.doubleValue())).subtract(BigDecimal.ONE);
                            if (rank == 1) {
                                dcg = numerator;
                            } else {
                                double den = Math.log(rank + 1) / Math.log(2);
                                dcg = dcg.add(numerator.divide(new BigDecimal(den), 2, RoundingMode.FLOOR));
                            }
                        });
            }

            @Override
            public BigDecimal value() {
                if (totalHits == 0) {
                    return relevantDocuments.size() == 0 ? BigDecimal.ONE : BigDecimal.ZERO;
                }

                final BigDecimal idealDcg = idealDcg(relevantDocuments);
                if (dcg.equals(BigDecimal.ZERO) && idealDcg.equals(BigDecimal.ZERO)) {
                    return BigDecimal.ZERO;
                }

                return dcg.divide(idealDcg, 2, RoundingMode.FLOOR);
            }
        };
    }

    private BigDecimal idealDcg(final JsonNode relevantDocuments) {
        final int windowSize = Math.min(relevantDocuments.size(), k);
        final double[] gains = new double[windowSize];

        final Map<BigDecimal, List<JsonNode>> groups =
                StreamSupport.stream(relevantDocuments.spliterator(), false)
                                .collect(groupingBy(doc -> gainOrRatingNode(doc).map(JsonNode::decimalValue).orElse(fairgrade)));

        Set<BigDecimal> ratingValues = groups.keySet();
        List<BigDecimal> ratingsSorted = new ArrayList<>(ratingValues);
        ratingsSorted.sort(Collections.reverseOrder());
        int startIndex = 0;
        for (BigDecimal ratingValue : ratingsSorted) {
            if (startIndex < windowSize) {
                List<JsonNode> docsPerRating = groups.get(ratingValue);
                int endIndex = startIndex + docsPerRating.size();
                Arrays.fill(gains, startIndex, Math.min(windowSize, endIndex), ratingValue.doubleValue());
                startIndex = endIndex;
            }
        }
        
        BigDecimal result = BigDecimal.ZERO;
        for (int i = 1; i <= gains.length; i++) {
            BigDecimal num = BigDecimal.valueOf(Math.pow(TWO.doubleValue(), gains[i-1])).subtract(BigDecimal.ONE);
            double den = Math.log(i + 1) / Math.log(2);
            result = result.add((num.divide(new BigDecimal(den), 2, RoundingMode.FLOOR)));
        }

        return result;
    }
}