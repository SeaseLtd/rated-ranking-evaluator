package io.sease.rre.core.domain.metrics;

import java.math.BigDecimal;
import java.util.Collection;
import java.util.Map;

/**
 * Singleton utility class for instantiating the metric class manager,
 * and managing metric configuration details.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class MetricClassConfigurationManager {

    private static MetricClassConfigurationManager INSTANCE = new MetricClassConfigurationManager();

    private BigDecimal defaultMaximumGrade = BigDecimal.valueOf(3);
    private BigDecimal defaultMissingGrade = BigDecimal.valueOf(2);

    public static MetricClassConfigurationManager getInstance() {
        return INSTANCE;
    }

    /**
     * Build the appropriate {@link MetricClassManager} for the metric
     * configuration passed.
     *
     * @param metrics              the simple metric configurations - a list of metric classes.
     * @param parameterizedMetrics the parameterized metric configuration, consisting
     *                             of class names and additional configuration.
     * @return a {@link MetricClassManager} that can instantiate all of the
     * configured metrics.
     */
    @SuppressWarnings("rawtypes")
    public MetricClassManager buildMetricClassManager(final Collection<String> metrics, final Map<String, Map> parameterizedMetrics) {
        final MetricClassManager metricClassManager;
        if (parameterizedMetrics == null || parameterizedMetrics.isEmpty()) {
            metricClassManager = new SimpleMetricClassManager(metrics);
        } else {
            metricClassManager = new ParameterizedMetricClassManager(metrics, parameterizedMetrics);
        }
        return metricClassManager;
    }

    /**
     * @return the default maximum grade to use when evaluating metrics. May be
     * overridden in parameterized metric configuration.
     */
    public BigDecimal getDefaultMaximumGrade() {
        return defaultMaximumGrade;
    }

    /**
     * Set the default maximum grade to use when evaluating metrics.
     *
     * @param defaultMaximumGrade the grade to use.
     * @return the singleton manager instance.
     */
    public MetricClassConfigurationManager setDefaultMaximumGrade(final float defaultMaximumGrade) {
        this.defaultMaximumGrade = BigDecimal.valueOf(defaultMaximumGrade);
        return this;
    }

    /**
     * @return the default grade to use when evaluating metrics, and no judgement
     * is present for the current document. May be overridden in parameterized
     * metric configuration.
     */
    public BigDecimal getDefaultMissingGrade() {
        return defaultMissingGrade;
    }

    /**
     * Set the default missing judgement grade to use when evaluating metrics.
     *
     * @param defaultMissingGrade the grade to use.
     * @return the singleton manager instance.
     */
    public MetricClassConfigurationManager setDefaultMissingGrade(final float defaultMissingGrade) {
        this.defaultMissingGrade = BigDecimal.valueOf(defaultMissingGrade);
        return this;
    }
}
