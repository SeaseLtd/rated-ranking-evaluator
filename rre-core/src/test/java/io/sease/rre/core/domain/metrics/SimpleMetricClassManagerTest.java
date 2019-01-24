package io.sease.rre.core.domain.metrics;

import org.junit.Test;

import java.util.Arrays;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/**
 * Unit tests for the SimpleMetricClassManager class.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class SimpleMetricClassManagerTest {

    private static final String[] METRICS = new String[]{
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne",
            "non.existent.DummyMetric",
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtK"
    };

    private MetricClassManager manager = new SimpleMetricClassManager(Arrays.asList(METRICS));

    @Test
    public void canInstantiateSimpleMetric() throws Exception {
        Metric m = manager.instantiateMetric("io.sease.rre.core.domain.metrics.impl.PrecisionAtOne");

        assertNotNull(m);
        assertTrue(m instanceof io.sease.rre.core.domain.metrics.impl.PrecisionAtOne);
    }

    @Test(expected = IllegalArgumentException.class)
    public void throwsExceptionForUndefinedMetric() throws Exception {
        manager.instantiateMetric("blah.blah.NoMetric");
    }

    @Test(expected = IllegalArgumentException.class)
    public void throwsExceptionForNonExistentMetric() throws Exception {
        manager.instantiateMetric("non.existent.DummyMetric");
    }

    @Test(expected = InstantiationException.class)
    public void throwsExceptionForMetricRequiringConfig() throws Exception {
        manager.instantiateMetric("io.sease.rre.core.domain.metrics.impl.PrecisionAtK");
    }
}
