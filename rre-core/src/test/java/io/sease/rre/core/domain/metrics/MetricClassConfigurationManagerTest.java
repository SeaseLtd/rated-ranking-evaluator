package io.sease.rre.core.domain.metrics;

import org.junit.Test;

import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Unit tests for the MetricClassManagerFactory class.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class MetricClassConfigurationManagerTest {

    private final MetricClassConfigurationManager factory = MetricClassConfigurationManager.getInstance();

    private static final Collection<String> METRICS = Arrays.asList(
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne",
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtK"
    );


    @Test
    public void returnsSimpleMetricManager_whenParameterizedMetricsAreNull() {
        assertThat(factory.buildMetricClassManager(METRICS, null)).isInstanceOf(SimpleMetricClassManager.class);
    }

    @Test
    public void returnsSimpleMetricManager_whenParameterizedMetricsIsEmpty() {
        assertThat(factory.buildMetricClassManager(METRICS, new HashMap<>())).isInstanceOf(SimpleMetricClassManager.class);
    }

    @Test
    @SuppressWarnings({"unchecked", "rawtypes"})
    public void returnsParameterizedMetricManager_whenParameterizedMetricsSet() {
        final Map precisionAtFiveConfig = new HashMap();
        precisionAtFiveConfig.put("class", "io.sease.rre.core.domain.metrics.impl.PrecisionAtK");
        precisionAtFiveConfig.put("v", 5);
        final Map<String, Map> parameterizedConfig = new HashMap<>();
        parameterizedConfig.put("pAt5", precisionAtFiveConfig);

        MetricClassManager test = factory.buildMetricClassManager(METRICS, parameterizedConfig);

        assertThat(test).isInstanceOf(ParameterizedMetricClassManager.class);
    }
}
