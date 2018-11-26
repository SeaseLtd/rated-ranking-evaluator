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
