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
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Supertype layer for all precision at X metrics.
 *
 * @author agazzarini
 * @since 1.0
 */
public class PrecisionAtK extends Metric {
    private final int k;

    /**
     * Builds a new AveragePrecision at X metric.
     *
     * @param k the precision bound.
     */
    PrecisionAtK(@JsonProperty("k") final int k) {
        super("P@" + k);
        this.k = k;
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            private final List<Map<String, Object>> collected = new ArrayList<>();

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                if (rank <= k && judgment(id(hit)).isPresent()) {
                    collected.add(hit);
                }
            }

            @Override
            public BigDecimal value() {
                if (totalHits == 0) {
                    return relevantDocuments.size() == 0 ? BigDecimal.ONE : BigDecimal.ZERO;
                }
                return collected.stream()
                        .map(hit -> BigDecimal.ONE)
                        .reduce(BigDecimal.ZERO, BigDecimal::add)
                        .divide(new BigDecimal(Math.min(totalHits, k)), 2, RoundingMode.HALF_UP);
            }
        };
    }

    @Override
    public int getRequiredResults() {
        return k;
    }
}