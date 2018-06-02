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
import java.util.stream.StreamSupport;

import static io.sease.rre.maven.plugin.report.Utility.all;
import static java.util.stream.Collectors.toList;

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

        final JsonNode evaluationData = evaluationAsJson();
        final EvaluationMetadata metadata = evaluationMetadata(evaluationData);

        formats.parallelStream()
                .map(formatters::get)
                .filter(Objects::nonNull)
                .forEach(formatter -> formatter.writeReport(evaluationAsJson(), metadata, locale, this));
    }

    private EvaluationMetadata evaluationMetadata(final JsonNode evaluationData) {
        final List<String> metrics =
                all(evaluationData, "corpora")
                        .limit(1)
                        .map(corpusNode -> corpusNode.get("metrics"))
                        .flatMap(metricsNode -> StreamSupport.stream(Spliterators.spliteratorUnknownSize(metricsNode.fieldNames(), Spliterator.ORDERED), false))
                        .collect(toList());

        final List<String> versions =
                all(evaluationData, "corpora")
                        .limit(1)
                        .map(corpusNode -> corpusNode.get("metrics").iterator().next().get("versions"))
                        .flatMap(versionsNode -> StreamSupport.stream(Spliterators.spliteratorUnknownSize(versionsNode.fieldNames(), Spliterator.ORDERED), false))
                        .collect(toList());

        return new EvaluationMetadata(versions, metrics);
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