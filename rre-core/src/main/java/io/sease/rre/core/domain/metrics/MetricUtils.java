package io.sease.rre.core.domain.metrics;

import java.util.HashMap;
import java.util.Map;

/**
 * Utility methods for manipulating Metric implementations.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public abstract class MetricUtils {

    // Map of name values which could be used in a database/search engine
    private static final Map<String, String> SANITISED_NAME_MAP = new HashMap<>();

    static {
        SANITISED_NAME_MAP.put("AP", "ap");
        SANITISED_NAME_MAP.put("F0.5", "f0Point5");
        SANITISED_NAME_MAP.put("F1", "f1");
        SANITISED_NAME_MAP.put("F2", "f2");
        SANITISED_NAME_MAP.put("NDCG@10", "ndcgAt10");
        SANITISED_NAME_MAP.put("P", "p");
        SANITISED_NAME_MAP.put("P@1", "pAt1");
        SANITISED_NAME_MAP.put("P@2", "pAt2");
        SANITISED_NAME_MAP.put("P@3", "pAt3");
        SANITISED_NAME_MAP.put("P@10", "pAt10");
        SANITISED_NAME_MAP.put("R", "r");
        SANITISED_NAME_MAP.put("RR@10", "rrAt10");
    }

    /**
     * Get the sanitised name for a {@link Metric} - eg. one that could be
     * used in a database or search engine field name.
     * <p>
     * Names will be camel-cased, for the most part, with '@' and '.' symbols
     * converted to words.
     *
     * @param m the metric.
     * @return the sanitised version of the metric name.
     */
    public static String sanitiseName(final Metric m) {
        final String ret;

        if (SANITISED_NAME_MAP.containsKey(m.getName())) {
            ret = SANITISED_NAME_MAP.get(m.getName());
        } else {
            // Do some basic sanitisation ourselves
            ret = m.getName().toLowerCase()
                    .replace("@", "At")
                    .replace(".", "Point");
        }

        return ret;
    }
}
