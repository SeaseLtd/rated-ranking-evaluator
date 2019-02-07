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

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.MetricUtils;
import io.sease.rre.core.domain.metrics.ValueFactory;
import io.sease.rre.core.domain.metrics.impl.F0_5;
import org.junit.Test;

import static org.junit.Assert.assertEquals;

/**
 * Unit tests for the MetricUtils class.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class MetricUtilsTest {

    @Test
    public void sanitiseName_returnsNameForKnownMetric() {
        final Metric m = new F0_5();
        final String sanitised = MetricUtils.sanitiseName(m);

        assertEquals("f0Point5", sanitised);
    }

    @Test
    public void sanitiseName_returnsNameForUnknownMetric() {
        final Metric m = new Metric("P@5.5") {
            @Override
            public ValueFactory createValueFactory(String version) {
                return null;
            }
        };
        final String sanitised = MetricUtils.sanitiseName(m);

        assertEquals("pAt5Point5", sanitised);
    }
}
