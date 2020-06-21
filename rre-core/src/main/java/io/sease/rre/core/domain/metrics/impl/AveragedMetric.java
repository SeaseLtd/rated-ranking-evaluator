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
import static io.sease.rre.Calculator.sum;

/**
 * A metric which is the mathematic mean of other collected metrics.
 *
 * @author agazzarini
 * @since 1.0
 */
public class AveragedMetric extends Metric {

    /**
     * A {@link ValueFactory} whose value can be changed.
     *
     * @author agazzarini
     * @since 1.0
     */
    class MutableValueFactory extends ValueFactory {
        private BigDecimal value = BigDecimal.ZERO;
        private final AtomicInteger counter = new AtomicInteger(0);

        /**
         * Builds a new (Metric) valueFactory with the given (metric) owner.
         *
         * @param owner the owner metric.
         */
        private MutableValueFactory(final Metric owner, final String version) {
            super(owner, version);
        }

        @Override
        public BigDecimal value() {
            return divide(value, counter.get());
        }

        /**
         * Collects a new (metric) value.
         *
         * @param additionalValue the collected value.
         */
        public void collect(final BigDecimal additionalValue) {
            value = sum(value, additionalValue);
            counter.incrementAndGet();
        }

        @Override
        public void collect(final Map<String, Object> hit, final int rank, final String version) {
            // Noop
        }
    }

    /**
     * Builds a new {@link AveragedMetric} instance with the given name.
     *
     * @param name the metric name.
     */
    public AveragedMetric(final String name) {
        super(name);
    }

    /**
     * Collects a new (metric) value.
     *
     * @param version         the version associated with the collected (metric) value.
     * @param additionalValue the collected value.
     */
    public synchronized void collect(final String version, final BigDecimal additionalValue) {
        ((MutableValueFactory)
                values.computeIfAbsent(version, this::createValueFactory))
                .collect(additionalValue);
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new MutableValueFactory(this, version);
    }
}