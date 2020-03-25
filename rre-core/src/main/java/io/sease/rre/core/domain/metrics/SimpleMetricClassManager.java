package io.sease.rre.core.domain.metrics;

import io.sease.rre.Func;

import java.util.*;

/**
 * Manager class for instantiating metrics configured for evaluation. This
 * implementation only handles metrics defined by their class names, and
 * not requiring any additional configuration - ie. those with zero-argument
 * constructors.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class SimpleMetricClassManager implements MetricClassManager {

    private final Collection<String> metricNames;
    private final Map<String, Class<? extends Metric>> metricClasses = new HashMap<>();

    SimpleMetricClassManager(Collection<String> metricClasses) {
        this.metricNames = new ArrayList<>(metricClasses);
    }

    @Override
    public Collection<String> getMetrics() {
        return Collections.unmodifiableCollection(metricNames);
    }

    @Override
    public Metric instantiateMetric(String metricName) throws IllegalArgumentException, InstantiationException {
        final Class<? extends Metric> klazz = findMetricClass(metricName);
        return instantiateMetricClass(klazz);
    }

    Class<? extends Metric> findMetricClass(String metricName) throws IllegalArgumentException {
        final Class<? extends Metric> klazz;
        if (metricClasses.containsKey(metricName)) {
            klazz = metricClasses.get(metricName);
        } else {
            klazz = Func.newMetricDefinition(metricName);
            metricClasses.put(metricName, klazz);
        }

        return klazz;
    }

    private Metric instantiateMetricClass(Class<? extends Metric> metricClass) throws InstantiationException {
        try {
            return metricClass.newInstance();
        } catch (IllegalAccessException e) {
            throw new InstantiationException("Illegal access of class " + metricClass);
        }
    }

    void addMetricNames(Collection<String> names) {
        metricNames.addAll(names);
    }
}
