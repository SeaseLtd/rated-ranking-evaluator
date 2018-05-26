package io.sease.rre.maven.plugin.report.formats;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.maven.plugin.report.RREReport;

import java.util.Locale;

public interface OutputFormat {
    void writeReport(JsonNode data, Locale locale, RREReport plugin);
}
