package io.sease.rre.server.domain;

import java.util.List;

public class EvaluationMetadata {
    public final List<String> versions;
    public final List<String> metrics;

    /**
     *
     * @param versions
     * @param metrics
     */
    public EvaluationMetadata(final List<String> versions, final List<String> metrics) {
        this.versions = versions;
        this.metrics = metrics;
    }

    public int howManyVersions() {
        return versions.size();
    }

    public int howManyMetrics() {
        return metrics.size();
    }

    public List<String> getVersions() {
        return versions;
    }

    public List<String> getMetrics() {
        return metrics;
    }
}