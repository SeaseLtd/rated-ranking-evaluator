package io.sease.rre.maven.plugin.report;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.maven.plugin.report.formats.OutputFormat;
import io.sease.rre.maven.plugin.report.formats.SpreadsheetOutputFormat;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.plugins.annotations.ResolutionScope;
import org.apache.maven.project.MavenProject;
import org.apache.maven.reporting.AbstractMavenReport;

import java.io.File;
import java.io.IOException;
import java.util.*;

@Mojo(name = "report",
      defaultPhase = LifecyclePhase.SITE,
      requiresDependencyResolution = ResolutionScope.RUNTIME,
      threadSafe = true)
public class RREReport extends AbstractMavenReport {
    /**
     * Practical reference to the Maven project
     */
    @Parameter(defaultValue = "${project}", readonly = true)
    private MavenProject project;

    @Parameter(name = "format", defaultValue = "html")
    List<String> formats;

    @Parameter(name = "endpoint", defaultValue = "http://127.0.0.1:9999")
    String endpoint;

    private Map<String, OutputFormat> formatters = new HashMap<>();
    {
        formatters.put("spreadsheet", new SpreadsheetOutputFormat());
    }

    final ObjectMapper mapper = new ObjectMapper();

    @Override
    protected void executeReport(final Locale locale) {
        formats.parallelStream()
                .map(formatters::get)
                .filter(Objects::nonNull)
                .forEach(formatter -> formatter.writeReport(evaluationAsJson(), locale, this));
    }

    @Override
    public String getOutputName() {
        return "rre-report";
    }

    @Override
    public String getName(final Locale locale) {
        return "Sease - Rated Ranking Evaluator Report";
    }

    @Override
    public String getDescription(Locale locale) {
        return "N.A.";
    }

    JsonNode evaluationAsJson() {
        try {
            return mapper.readTree(evaluationOutputFile());
        } catch (final IOException exception) {
            throw new RuntimeException("Unable to load the RRE evaluation JSON payload. Are you sure RRE executed successfully?", exception);
        }
    }

    File evaluationOutputFile() {
        final File file = new File("target/rre/evaluation.json");
        if (!file.canRead()) {
            throw new RuntimeException("Unable to read RRE evaluation output file. Are you sure RRE executed successfully?");
        }
        return file;
    }


}