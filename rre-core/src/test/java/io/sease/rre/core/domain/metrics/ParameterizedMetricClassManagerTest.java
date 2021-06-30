package io.sease.rre.core.domain.metrics;

import org.junit.Test;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.*;

/**
 * Unit tests for the ParameterizedMetricClassManager.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
@SuppressWarnings("unchecked")
public class ParameterizedMetricClassManagerTest {

    private static final String[] METRICS = new String[]{
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne",
            "non.existent.DummyMetric",
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtK"
    };

    private MetricClassManager manager = new ParameterizedMetricClassManager(Arrays.asList(METRICS), null);

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
    public void throwsExceptionForMetricRequiringConfig_whenNoConfigSupplied() throws Exception {
        manager.instantiateMetric("io.sease.rre.core.domain.metrics.impl.PrecisionAtK");
    }

    @Test(expected = IllegalArgumentException.class)
    public void constructionFailsWhenClassDetailsMissing() throws Exception {
        final Map precisionAtFiveConfig = new HashMap();
        final Map<String, Map> metricConfiguration = new HashMap<>();
        metricConfiguration.put("pAt5", precisionAtFiveConfig);
        new ParameterizedMetricClassManager(Arrays.asList(METRICS), metricConfiguration);
    }

    @Test(expected = InstantiationException.class)
    public void throwsExceptionForParameterizedMetric_whenConfigIsWrong() throws Exception {
        final Map precisionAtFiveConfig = new HashMap();
        precisionAtFiveConfig.put("class", "io.sease.rre.core.domain.metrics.impl.PrecisionAtK");
        precisionAtFiveConfig.put("v", 5);
        final Map<String, Map> metricConfiguration = new HashMap<>();
        metricConfiguration.put("pAt5", precisionAtFiveConfig);
        final MetricClassManager manager = new ParameterizedMetricClassManager(Arrays.asList(METRICS), metricConfiguration);
        manager.instantiateMetric("pAt5");
    }

    @Test
    public void canInstantiateParameterizedMetric() throws Exception {
        final Map precisionAtFiveConfig = new HashMap();
        precisionAtFiveConfig.put("class", "io.sease.rre.core.domain.metrics.impl.PrecisionAtK");
        precisionAtFiveConfig.put("k", 5);
        final Map<String, Map> metricConfiguration = new HashMap<>();
        metricConfiguration.put("pAt5", precisionAtFiveConfig);
        final MetricClassManager manager = new ParameterizedMetricClassManager(Arrays.asList(METRICS), metricConfiguration);
        Metric m = manager.instantiateMetric("pAt5");

        assertNotNull(m);
        assertTrue(m instanceof io.sease.rre.core.domain.metrics.impl.PrecisionAtK);
        assertEquals("Precision@5", m.getName());
    }
}
