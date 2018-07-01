package io.sease.rre.maven.plugin.report.domain;

import java.util.List;

/**
 * Basic metadata about an evaluation result.
 *
 * @author agazzarini
 * @since 1.0
 */
public class EvaluationMetadata {
    public final List<String> versions;
    public final List<String> metrics;

    /**
     * Builds a new metadata with the given values.
     *
     * @param versions the available versions in the evaluation data.
     * @param metrics  the available metrics in the evaluation data.
     */
    public EvaluationMetadata(final List<String> versions, final List<String> metrics) {
        this.versions = versions;
        this.metrics = metrics;
    }

    /**
     * Returns the total number of versions used in this evaluation cycle.
     *
     * @return the total number of versions used in this evaluation cycle.
     */
    public int howManyVersions() {
        return versions.size();
    }

    /**
     * Returns the total number of metrics used in this evaluation cycle.
     *
     * @return the total number of metrics used in this evaluation cycle.
     */
    public int howManyMetrics() {
        return metrics.size();
    }
}