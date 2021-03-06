/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package io.sease.rre.maven.plugin.report;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.maven.plugin.report.domain.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.formats.OutputFormat;
import io.sease.rre.maven.plugin.report.formats.impl.RREOutputFormat;
import io.sease.rre.maven.plugin.report.formats.impl.SpreadsheetOutputFormat;
import io.sease.rre.maven.plugin.report.formats.impl.UrlRREOutputFormat;
import io.sease.rre.persistence.impl.JsonPersistenceHandler;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.reporting.AbstractMavenReport;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Spliterator;

import static io.sease.rre.maven.plugin.report.Utility.all;
import static java.util.Optional.ofNullable;
import static java.util.Spliterators.spliteratorUnknownSize;
import static java.util.stream.Collectors.toList;
import static java.util.stream.StreamSupport.stream;

/**
 * A Maven plugin for creating useful / human-readable reports from the RRE evaluation results.
 *
 * @author agazzarini
 * @since 1.0
 */
@Mojo(name = "report", inheritByDefault = false)
public class RREMavenReport extends AbstractMavenReport {
    @Parameter(name = "formats", defaultValue = "spreadsheet")
    List<String> formats;

    @Parameter(name = "endpoint", defaultValue = "http://127.0.0.1:8080")
    String endpoint;

    @Parameter(name="evaluationFile", defaultValue = JsonPersistenceHandler.DEFAULT_OUTPUT_FILE)
    String evaluationFile;

    private Map<String, OutputFormat> formatters = new HashMap<>();

    {
        formatters.put("spreadsheet", new SpreadsheetOutputFormat());
        formatters.put("rre-server", new RREOutputFormat());
        formatters.put("url-rre-server", new UrlRREOutputFormat());
    }

    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    protected void executeReport(final Locale locale) {
        final JsonNode evaluationData = evaluationAsJson();
        final JsonNode corpora = evaluationData.get("corpora");

        if (corpora == null || corpora.size() == 0) {
            getLog().info("No evaluation data has been generated - no reports will be produced.");
            return;
        }

        formats.parallelStream()
                .map(formatters::get)
                .filter(Objects::nonNull)
                .forEach(formatter ->
                        formatter.writeReport(
                                evaluationData,
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
                        .map(corpusNode -> ofNullable(corpusNode.get("metrics"))
                                                .map(JsonNode::iterator)
                                                .filter(Iterator::hasNext)
                                                .map(Iterator::next)
                                                .map(node -> node.get("versions"))
                                                .orElseGet(() -> new ObjectMapper().createObjectNode()))
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

    public String getEvaluationFile() {
        return evaluationFile;
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
        final File file = new File(evaluationFile);
        if (!file.canRead()) {
            throw new RuntimeException("Unable to read RRE evaluation output file. Are you sure RRE executed successfully?");
        }
        return file;
    }
}