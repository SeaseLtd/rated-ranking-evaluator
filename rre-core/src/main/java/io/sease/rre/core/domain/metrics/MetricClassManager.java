package io.sease.rre.core.domain.metrics;

import java.util.Collection;

/**
 * A MetricClassManager is used to supply the metrics available to the
 * evaluations.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public interface MetricClassManager {

    /**
     * Retrieve the list of metrics available to each evaluation. These may
     * be class names, or other strings which can be used to reference a
     * metric that requires further configuration - for example, multiple
     * instances of PrecisionAtK with different values for K.
     *
     * @return the available metrics.
     */
    Collection<String> getMetrics();

    /**
     * Instantiate a metric, using the name given in the {@link #getMetrics()}
     * list, and initialising with any additional configuration detail
     * available.
     *
     * @param metricName the name of the metric to be instantiated.
     * @return an instance of a {@link Metric}.
     * @throws IllegalArgumentException if the metric is not in the configured
     *                                  list, or the class cannot be found.
     * @throws InstantiationException   if the metric cannot be instantiated.
     */
   Metric instantiateMetric(String metricName) throws IllegalArgumentException, InstantiationException;
}
