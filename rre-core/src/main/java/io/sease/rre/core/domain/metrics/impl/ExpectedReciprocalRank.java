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
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.StreamSupport;

import static io.sease.rre.Func.gainOrRatingNode;
import static java.util.Collections.emptyList;
import static java.util.stream.Collectors.groupingBy;

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
     */
    public ExpectedReciprocalRank(@JsonProperty("maxgrade") final float maxgrade, @JsonProperty("k") final int k) {
        super("ERR" + "@" + k);
        this.fairgrade = BigDecimal.valueOf(Math.round(maxgrade/2));
        this.maxgrade = BigDecimal.valueOf(maxgrade);
        this.k = k;
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            private BigDecimal ERR = BigDecimal.ZERO;
            private BigDecimal trust = BigDecimal.ONE;
            private BigDecimal value = fairgrade;
            private int totalHits = 0;
            private int totalDocs = 0;

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                if (++totalDocs>k) return;
                value = fairgrade;
                judgment(id(hit))
                    .ifPresent(judgment -> {
                        value = gainOrRatingNode(judgment).map(JsonNode::decimalValue).orElse(fairgrade);
                        totalHits++;
                    });
                BigDecimal r = BigDecimal.valueOf(rank);
                BigDecimal usefulness = gain(value,maxgrade);
                BigDecimal discounted = usefulness.divide(r,8,RoundingMode.HALF_UP);
                ERR = ERR.add(trust.multiply(discounted));
                trust = trust.multiply(BigDecimal.ONE.subtract(usefulness));
                //System.out.println(String.valueOf(rank) + " -> " + value.toPlainString());
                //System.out.println(value.toPlainString());
            }

            @Override
            public BigDecimal value() {
                if (totalHits==0) {
                    return (totalDocs == 0) ? BigDecimal.ONE : BigDecimal.ZERO;
                }
                return ERR;
            }
        };
    }

    private BigDecimal gain(BigDecimal grade, BigDecimal max) {
        final BigDecimal numer = TWO.pow(grade.intValue()).subtract(BigDecimal.ONE);
        final BigDecimal denom = TWO.pow(max.intValue());
        if (denom.equals(BigDecimal.ZERO)) {
            return BigDecimal.ZERO;
        }
        return numer.divide(denom,8,RoundingMode.HALF_UP);
    }
}
