package io.sease.rre.maven.plugin.report;

import java.util.List;

public class EvaluationMetadata {
    public final List<String> versions;
    public final List<String> metrics;


    public EvaluationMetadata(List<String> versions, List<String> metrics) {
        this.versions = versions;
        this.metrics = metrics;
    }

    public int howManyVersions() {
        return versions.size();
    }

    public int howManyMetrics() {
        return metrics.size();
    }
}