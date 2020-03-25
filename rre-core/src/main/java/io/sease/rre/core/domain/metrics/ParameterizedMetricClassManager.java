package io.sease.rre.core.domain.metrics;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.IOException;
import java.util.*;

/**
 * A MetricClassManager implementation which allows both simple
 * (non-configurable) and configurable metrics to be constructed using
 * supplied parameters.
 * <p>
 * The parameterized metrics should have a constructor with {@code JsonProperty}
 * annotations indicating how the configuration should be used.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class ParameterizedMetricClassManager extends SimpleMetricClassManager implements MetricClassManager {

    private final static Logger LOGGER = LogManager.getLogger(ParameterizedMetricClassManager.class);

    public static final String NAME_KEY = "name";
    public static final String MAXIMUM_GRADE_KEY = "maximumGrade";
    public static final String MISSING_GRADE_KEY = "missingGrade";

    private static final String METRIC_CLASS_KEY = "class";

    private final Map<String, Map<String, Object>> metricConfiguration;
    private final Map<String, String> metricClasses;

    @SuppressWarnings("rawtypes")
    ParameterizedMetricClassManager(Collection<String> metricNames, Map<String, Map> metricConfiguration) {
        super(metricNames);
        this.metricClasses = extractParameterizedClassNames(metricConfiguration);
        this.metricConfiguration = convertMetricConfiguration(metricConfiguration);
        addMetricNames(metricClasses.keySet());
    }

    /**
     * Extract the class names for each parameterized metric from the incoming map.
     * Doubles up as a check that the parameterized configuration contains a classname
     * for each required metric.
     *
     * @param incoming the incoming metric configurations.
     * @return a map of String:String, containing the class for each parameterized
     * metric we need to build.
     * @throws IllegalArgumentException if any of the configurations do not have a
     *                                  class property.
     */
    @SuppressWarnings("rawtypes")
    private Map<String, String> extractParameterizedClassNames(final Map<String, Map> incoming) throws IllegalArgumentException {
        final Map<String, String> classNames;
        if (incoming == null) {
            classNames = Collections.emptyMap();
        } else {
            classNames = new HashMap<>();
            incoming.forEach((metricName, configMap) -> {
                if (!configMap.containsKey(METRIC_CLASS_KEY)) {
                    throw new IllegalArgumentException("No class set for metric " + metricName);
                } else {
                    classNames.put(metricName, (String) configMap.get(METRIC_CLASS_KEY));
                }
            });
        }
        return classNames;
    }

    /**
     * Extract the configuration properties for each parameterized metric from
     * the incoming map, stripping out the implementation class name as we go,
     * and convert them to a map of String:Object items.
     *
     * @param incoming the incoming metric configurations.
     * @return an equivalent map containing configuration that can be used to
     * construct a Metric without stripping any content.
     */
    @SuppressWarnings({"unchecked", "rawtypes"})
    private Map<String, Map<String, Object>> convertMetricConfiguration(final Map<String, Map> incoming) {
        final Map<String, Map<String, Object>> configurations;
        if (incoming == null) {
            configurations = Collections.emptyMap();
        } else {
            configurations = new HashMap<>();
            incoming.forEach((metricName, configOptions) -> {
                Map<String, Object> config = new HashMap<>();
                configOptions.forEach((k, v) -> {
                    if (!k.equals(METRIC_CLASS_KEY)) {
                        config.put((String) k, v);
                    }
                });
                configurations.put(metricName, config);
            });
        }
        return configurations;
    }

    @Override
    public Metric instantiateMetric(String metricName) throws IllegalArgumentException, InstantiationException {
        final Metric metric;
        if (!metricConfiguration.containsKey(metricName)) {
            // Simple metric - use superclass to build
            metric = super.instantiateMetric(metricName);
        } else {
            // Parameterized metric - firstly identify the class
            final String className = metricClasses.get(metricName);
            final Class<? extends Metric> klazz = findMetricClass(className);
            metric = instantiateClassWithConfiguration(klazz, metricConfiguration.get(metricName));
        }
        return metric;
    }

    private Metric instantiateClassWithConfiguration(final Class<? extends Metric> metricClass,
                                                     final Map<String, Object> metricConfiguration) throws InstantiationException {
        final Metric m;
        try {
            /* We build by converting the config to JSON, then constructing the
             * required class from the JSON string - this is *much* easier than
             * trying to find the correct constructor, etc., ourselves. */
            final ObjectMapper mapper = new ObjectMapper();
            final String configJson = mapper.writeValueAsString(metricConfiguration);
            m = mapper.readValue(configJson, metricClass);
        } catch (IOException e) {
            // Either the map could not be serialized to JSON, or the JSON has properties that don't match the constructor
            LOGGER.error("Caught IO exception instantiating configured class {} :: {}", metricClass.getName(), e.getMessage());
            throw new InstantiationException(e.getMessage());
        }
        return m;
    }
}
