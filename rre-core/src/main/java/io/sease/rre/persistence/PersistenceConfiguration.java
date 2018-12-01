package io.sease.rre.persistence;

import java.util.HashMap;
import java.util.Map;

/**
 * Configuration details for the persistence manager.
 * <p>
 * Configuration consists of a set of handler names, mapped to their
 * implementation classes. The handler names are then used to refer to
 * specific sets of configuration details, allowing the same implementation
 * to be used multiple times with separate destinations (for example).
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class PersistenceConfiguration {

    /**
     * Default configuration object, with configuration for persisting to
     * a single JSON output file.
     */
    public static final PersistenceConfiguration DEFAULT_CONFIG = defaultConfiguration();

    private boolean useTimestampAsVersion = false;
    private Map<String, String> handlers;
    // Supplying type params for nested map breaks Maven initialisation
    private Map<String, Map> handlerConfiguration;

    @SuppressWarnings("unused")
    public PersistenceConfiguration() {
        // Do nothing - required for Maven initialisation
    }

    private PersistenceConfiguration(boolean useTimestampAsVersion,
                                     Map<String, String> handlers,
                                     Map<String, Map> handlerConfiguration) {
        this.useTimestampAsVersion = useTimestampAsVersion;
        this.handlers = handlers;
        this.handlerConfiguration = handlerConfiguration;
    }

    /**
     * Should the persistence framework use a timestamp in place of the
     * configuration version? This timestamp should be consistent for
     * the duration of the evaluation.
     * <p>
     * This will take effect when there is only one configuration set
     * available - eg. for users who modify the same configuration set
     * rather than creating a separate one each iteration.
     *
     * @return {@code true} if a timestamp should be used in place of the
     * version string when persisting query output.
     */
    public boolean isUseTimestampAsVersion() {
        return useTimestampAsVersion;
    }

    /**
     * @return a map of handler name to implementation classes.
     */
    public Map<String, String> getHandlers() {
        return handlers;
    }

    /**
     * @return a map of handler name to a map containing configuration
     * details for the handler.
     */
    public Map<String, Map> getHandlerConfiguration() {
        return handlerConfiguration;
    }

    /**
     * Get the configuration for an individual handler, returning a map of
     * configuration items keyed by the String value of their name. If there
     * is no configuration, an empty map will be returned.
     *
     * @param name the name of the handler whose configuration is required.
     * @return a String:Object map containing the configuration. Never
     * {@code null}.
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getHandlerConfigurationByName(String name) {
        Map<String, Object> configMap = new HashMap<>();

        if (handlerConfiguration.get(name) != null) {
            handlerConfiguration.get(name).forEach((k, v) -> configMap.put(String.valueOf(k), v));
        }

        return configMap;
    }

    /**
     * Build a default PersistenceConfiguration, with handlers set to write
     * to the standard JSON output file.
     *
     * @return a PersistenceConfiguration object.
     */
    private static PersistenceConfiguration defaultConfiguration() {
        final String jsonKey = "json";
        Map<String, String> handlers = new HashMap<>();
        handlers.put(jsonKey, "io.sease.rre.persistence.impl.JsonPersistenceHandler");
        Map<String, Object> jsonConfig = new HashMap<>();
        jsonConfig.put("outputFile", "target/rre/evaluation.json");
        Map<String, Map> handlerConfig = new HashMap<>();
        handlerConfig.put(jsonKey, jsonConfig);

        return new PersistenceConfiguration(false, handlers, handlerConfig);
    }
}
