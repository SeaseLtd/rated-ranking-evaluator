package io.sease.rre.core.domain.metrics;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * Singleton utility class for instantiating the metric class manager,
 * and managing metric configuration details.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class MetricClassManagerFactory {

    private static MetricClassManagerFactory instance;

    private BigDecimal defaultMaximumGrade = BigDecimal.valueOf(3);
    private BigDecimal defaultMissingGrade = BigDecimal.valueOf(2);

    private MetricClassManagerFactory() {
        // Private constructor
    }

    public static MetricClassManagerFactory getInstance() {
        if (instance == null) {
            instance = new MetricClassManagerFactory();
        }
        return instance;
    }

    public MetricClassManager buildMetricClassManager(List<String> metrics, Map<String, Map> parameterizedMetrics) {
        final MetricClassManager metricClassManager;
        if (parameterizedMetrics == null || parameterizedMetrics.isEmpty()) {
            metricClassManager = new SimpleMetricClassManager(metrics);
        } else {
            metricClassManager = new ParameterizedMetricClassManager(metrics, parameterizedMetrics);
        }
        return metricClassManager;
    }

    public BigDecimal getDefaultMaximumGrade() {
        return defaultMaximumGrade;
    }

    public MetricClassManagerFactory setDefaultMaximumGrade(BigDecimal defaultMaximumGrade) {
        this.defaultMaximumGrade = defaultMaximumGrade;
        return this;
    }

    public BigDecimal getDefaultMissingGrade() {
        return defaultMissingGrade;
    }

    public MetricClassManagerFactory setDefaultMissingGrade(BigDecimal defaultMissingGrade) {
        this.defaultMissingGrade = defaultMissingGrade;
        return this;
    }
}
