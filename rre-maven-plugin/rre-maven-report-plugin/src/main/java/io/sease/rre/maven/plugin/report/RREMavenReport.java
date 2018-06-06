package io.sease.rre.maven.plugin.report;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.maven.plugin.report.domain.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.formats.OutputFormat;
import io.sease.rre.maven.plugin.report.formats.impl.RREOutputFormat;
import io.sease.rre.maven.plugin.report.formats.impl.SpreadsheetOutputFormat;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.plugins.annotations.ResolutionScope;
import org.apache.maven.reporting.AbstractMavenReport;

import java.io.File;
import java.io.IOException;
import java.util.*;

import static io.sease.rre.maven.plugin.report.Utility.all;
import static java.util.Spliterators.spliteratorUnknownSize;
import static java.util.stream.Collectors.toList;
import static java.util.stream.StreamSupport.stream;

/**
 * A Maven plugin for creating useful / human-readable reports from the RRE evaluation results.
 *
 * @author agazzarini
 * @since 1.0
 */
@Mojo(name = "report",
      defaultPhase = LifecyclePhase.SITE,
      requiresDependencyResolution = ResolutionScope.RUNTIME,
      threadSafe = true)
public class RREMavenReport extends AbstractMavenReport {
    @Parameter(name = "format", defaultValue = "spreadsheet")
    List<String> formats;

    @Parameter(name = "endpoint", defaultValue = "http://127.0.0.1:8080")
    String endpoint;

    private Map<String, OutputFormat> formatters = new HashMap<>();
    {
        formatters.put("spreadsheet", new SpreadsheetOutputFormat());
        formatters.put("rre-server", new RREOutputFormat());
    }

    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    protected void executeReport(final Locale locale) {
        final JsonNode evaluationData = evaluationAsJson();
        formats.parallelStream()
                .map(formatters::get)
                .filter(Objects::nonNull)
                .forEach(formatter ->
                            formatter.writeReport(
                                        evaluationAsJson(),
                                        evaluationMetadata(evaluationData),
                                        locale,
                                        this));
    }

    /**
     * Returns the metadata extracted from the current evaluation.
     *
     * @param evaluationData the evaluation result.
     * @return the metadata extracted from the current evaluation.
     */
    private EvaluationMetadata evaluationMetadata(final JsonNode evaluationData) {
        final List<String> metrics =
                all(evaluationData, "corpora")
                        .limit(1)
                        .map(corpusNode -> corpusNode.get("metrics"))
                        .flatMap(metricsNode -> stream(spliteratorUnknownSize(metricsNode.fieldNames(), Spliterator.ORDERED), false))
                        .collect(toList());

        final List<String> versions =
                all(evaluationData, "corpora")
                        .limit(1)
                        .map(corpusNode -> corpusNode.get("metrics").iterator().next().get("versions"))
                        .flatMap(versionsNode -> stream(spliteratorUnknownSize(versionsNode.fieldNames(), Spliterator.ORDERED), false))
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
    public String getDescription(final Locale locale) {
        return "N.A.";
    }

    /**
     * Returns the endpoint of a running RRE server.
     * Note that this is supposed to be used only in conjunction with the corresponding output format.
     *
     * @return the endpoint of a running RRE server.
     */
    public String getEndpoint() {
        return endpoint;
    }

    /**
     * Returns the evaluation data as a JSON object.
     *
     * @return the evaluation data as a JSON object.
     */
    private JsonNode evaluationAsJson() {
        try {
            return mapper.readTree(evaluationOutputFile());
        } catch (final IOException exception) {
            throw new RuntimeException("Unable to load the RRE evaluation JSON payload. Are you sure RRE executed successfully?", exception);
        }
    }

    /**
     * Returns a file reference to the evaluation output.
     *
     * @return a file reference to the evaluation output.
     */
    File evaluationOutputFile() {
        final File file = new File("target/rre/evaluation.json");
        if (!file.canRead()) {
            throw new RuntimeException("Unable to read RRE evaluation output file. Are you sure RRE executed successfully?");
        }
        return file;
    }
}