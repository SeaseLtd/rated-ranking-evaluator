package io.sease.rre.maven.plugin.report.formats;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.maven.plugin.report.domain.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.RREMavenReport;

import java.util.Locale;

/**
 * Interface definition / contract of an RRE output format.
 *
 * @author agazzarini
 * @since 1.0
 */
public interface OutputFormat {
    /**
     * Writes out the report, according with the logic of this concrete implementor.
     *
     * @param data the RRE evaluation result.
     * @param metadata the RRE evaluation metadata.
     * @param locale the current locale.
     * @param plugin the owning plugin.
     */
    void writeReport(JsonNode data, EvaluationMetadata metadata, Locale locale, RREMavenReport plugin);
}
