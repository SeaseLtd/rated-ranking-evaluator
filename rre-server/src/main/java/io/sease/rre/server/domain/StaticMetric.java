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
package io.sease.rre.server.domain;

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.Map;

/**
 * A metric holder, which is not itself a metric but contains some metric data (actually name and value).
 * This is needed on RRE server side because here we no longer have the metrics definitions (in terms of classes / subclasses)
 * defined on the RRE core, but at the same time we need a general way to deserialize them in an object structure.
 *
 * @author agazzarini
 * @since 1.0
 */
public class StaticMetric extends Metric {

    /**
     * Builds a new {@link Metric} with the given mnemonic name.
     *
     * @param name the metric name.
     */
    public StaticMetric(final String name) {
        super(name);
    }

    public void collect(final String version, final BigDecimal value) {
        values.computeIfAbsent(version, v ->
                new ValueFactory(this, version) {
                    @Override
                    public BigDecimal value() {
                        return value;
                    }

                    @Override
                    public void collect(Map<String, Object> hit, int rank, String version) {
                        // Nothing to be done here...
                    }
                }
        );
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            @Override
            public BigDecimal value() {
                return BigDecimal.TEN;
            }

            @Override
            public void collect(Map<String, Object> hit, int rank, String version) {
                // Nothing to be done here...
            }
        };
    }
}