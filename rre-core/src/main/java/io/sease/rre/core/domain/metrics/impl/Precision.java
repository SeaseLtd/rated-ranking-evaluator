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

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.Calculator.divide;

/**
 * Precision is the fraction of the documents retrieved that are relevant to the user's information need.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Precision extends Metric {
    /**
     * Builds a new AveragePrecision metric.
     */
    public Precision() {
        super("P");
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            final AtomicInteger relevantItemsFound = new AtomicInteger();

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                judgment(id(hit)).ifPresent(relevantItem -> relevantItemsFound.incrementAndGet());
            }

            @Override
            public BigDecimal value() {
                if (totalHits == 0) {
                    return relevantDocuments.size() == 0 ? BigDecimal.ONE : BigDecimal.ZERO;
                }
                return divide(new BigDecimal(relevantItemsFound.get()), totalHits);
            }
        };
    }
}
