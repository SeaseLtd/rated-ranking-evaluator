package io.sease.rre.core;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.*;
import io.sease.rre.core.domain.metrics.CompoundMetric;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.event.MetricEvent;
import io.sease.rre.core.event.MetricEventListener;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;

import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

import static io.sease.rre.Utility.safe;
import static java.util.Arrays.stream;
import static java.util.stream.Collectors.toList;

/**
 * RRE core engine.
 * The engine is responsible for the whole evaluation process execution.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Engine {
    private final File configurationsFolder;
    private final File corporaFolder;
    private final File ratingsFolder;
    private final File templatesFolder;

    private final List<Class<? extends Metric>> availableMetricsDefs;
    private final List<Class<? extends CompoundMetric>> availableCompoundMetricsDefs;

    private final SearchPlatform platform;
    private final List<MetricEventListener> metricEventListeners = new ArrayList<>();

    /**
     * Builds a new {@link Engine} instance with the given data.
     *
     * @param platform the search platform in use.
     * @param configurationsFolderPath the configurations folder path.
     * @param corporaFolderPath the corpora folder path.
     * @param ratingsFolderPath the ratings folder path.
     * @param templatesFolderPath the query templates folder path.
     */
    public Engine(
            final SearchPlatform platform,
            final String configurationsFolderPath,
            final String corporaFolderPath,
            final String ratingsFolderPath,
            final String templatesFolderPath,
            final List<String> metrics,
            final List<String> compoundMetrics) {
        this.configurationsFolder = new File(configurationsFolderPath);
        this.corporaFolder = new File(corporaFolderPath);
        this.ratingsFolder = new File(ratingsFolderPath);
        this.templatesFolder = new File(templatesFolderPath);
        this.platform = platform;

        this.availableMetricsDefs =
                metrics.stream()
                        .map(this::newMetricDefinition)
                        .filter(Objects::nonNull)
                        .collect(toList());

        this.availableCompoundMetricsDefs =
                compoundMetrics.stream()
                        .map(this::newCompoundMetricDefinition)
                        .filter(Objects::nonNull)
                        .collect(toList());
    }

    private List<String> versions;

    /**
     * Executes the evaluation process.
     *
     * @param configuration the engine configuration.
     * @return the evaluation result.
     */
    @SuppressWarnings("unchecked")
    public Evaluation evaluate(final Map<String, Object> configuration){

        platform.beforeStart(configuration);
        platform.start();
        platform.afterStart();

        final Evaluation evaluation = new Evaluation();

        ratings().forEach(ratingsNode -> {
            final String indexName = ratingsNode.get("index").asText();
            final String idFieldName = ratingsNode.get("id_field").asText("id");
            final File data = new File(corporaFolder, ratingsNode.get("corpora_file").asText());

            if (!data.canRead()) {
                throw new IllegalArgumentException("Unable to read the corpus file " + data.getAbsolutePath());
            }

            prepareData(indexName, data);

            final Corpus corpus = evaluation.findOrCreate(data.getName(), Corpus::new);
            all(ratingsNode.get("topics"))
                    .forEach(topicNode -> {
                        final Topic topic = corpus.findOrCreate(topicNode.get("description").asText(), Topic::new);
                        all(topicNode.get("query_groups"))
                                .forEach(groupNode -> {
                                    final QueryGroup group =
                                            topic.findOrCreate(groupNode.get("name").asText(), QueryGroup::new);
                                    all(groupNode.get("queries"))
                                            .forEach(queryNode -> {
                                                final String query = query(queryNode);
                                                final Query queryEvaluation = group.findOrCreate(query, Query::new);
                                                final JsonNode relevantDocuments = groupNode.get("relevant_documents");

                                                queryEvaluation.prepare(availableMetrics(availableMetricsDefs, idFieldName, relevantDocuments, versions));

                                                versions.forEach(version -> {
                                                    final AtomicInteger rank = new AtomicInteger(1);
                                                    final QueryOrSearchResponse response =
                                                            platform.executeQuery(indexFqdn(indexName, version), query, Math.max(10, relevantDocuments.size()));

                                                    queryEvaluation.setTotalHits(response.totalHits(), version);
                                                    response.hits().forEach(hit -> queryEvaluation.collect(hit, rank.getAndIncrement(), version));
                                                });
                                            });
                                });
                    });
        });

        platform.beforeStop();

        return evaluation;
    }

    /**
     * Creates a new set of metrics.
     *
     * @param definitions the metrics definitions.
     * @param idFieldName the id fieldname.
     * @param relevantDocumentsMap the relevant documents for a given query.
     * @param versions the available versions for a given query.
     * @return a new metrics set for the current query evaluation.
     */
    private List<Metric> availableMetrics(
            final List<Class<? extends Metric>> definitions,
            final String idFieldName,
            final JsonNode relevantDocumentsMap,
            final List<String> versions) {
        return definitions
                .stream()
                .map(def -> {
                    try {
                        final Metric metric = def.newInstance();
                        metric.setIdFieldName(idFieldName);
                        metric.setRelevantDocuments(relevantDocumentsMap);
                        metric.setVersions(versions);
                        return metric;
                    } catch (final Exception exception) {
                        throw new IllegalArgumentException(exception);
                    }})
                .collect(toList());
    }

    private <L extends MetricEventListener> L withMetricEventListening(final L listener) {
        metricEventListeners.add(listener);
        return listener;
    }

    private void broadcast(final Metric metric, final String version) {
        final MetricEvent event = new MetricEvent(metric, version, this);
        metricEventListeners.forEach(listener -> listener.newMetricHasBeenComputed(event));
    }

    /**
     * Loads the query template associated with the given name.
     *
     * @param templateName the query template name.
     * @return the query template associated with the given name.
     */
    private String queryTemplate(final String templateName) {
        try {
            return new String(Files.readAllBytes(new File(templatesFolder, templateName).toPath()));
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    /**
     * Loads the ratings associated with the given name.
     *
     * @return the ratings / judgements for this evaluation suite.
     */
    private Stream<JsonNode> ratings() {
        final ObjectMapper mapper = new ObjectMapper();
        return stream(ratingsFolder.listFiles((dir, name) -> name.endsWith(".json")))
                .map(ratingFile -> {
                    try {
                        return mapper.readTree(ratingFile);
                    } catch (final IOException exception) {
                        throw new RuntimeException(exception);
                    }});
    }

    /**
     * Streams out all members of a given JSON node.
     *
     * @param source the parent JSON node.
     * @return a stream consisting of all children of the given JSON node.
     */
    private Stream<JsonNode> all(final JsonNode source) {
        return StreamSupport.stream(source.spliterator(), false);
    }

    @SuppressWarnings("unchecked")
    private Class<? extends Metric> newMetricDefinition(final String clazzName) {
        try {
            return (Class<? extends Metric>) Class.forName(clazzName);
        } catch (final Exception exception) {
            throw new IllegalArgumentException(exception);
        }
    }

    @SuppressWarnings("unchecked")
    private Class<? extends CompoundMetric> newCompoundMetricDefinition(final String clazzName) {
        try {
            return (Class<? extends CompoundMetric>) Class.forName(clazzName);
        } catch (final Exception exception) {
            throw new IllegalArgumentException(exception);
        }
    }

    private void prepareData(final String indexName, final File data) {
        final File [] versionFolders = safe(configurationsFolder.listFiles(file -> file.isDirectory() && !file.isHidden()));
        stream(versionFolders)
                .flatMap(versionFolder -> stream(safe(versionFolder.listFiles(file -> file.isDirectory() && !file.isHidden()))))
                .filter(folder -> folder.getName().equals(indexName))
                .forEach(folder -> platform.load(data, folder, indexFqdn(indexName, folder.getParentFile().getName())));

        this.versions = stream(versionFolders).map(File::getName).collect(toList());
    }

    private String indexFqdn(final String indexName, final String version) {
        return indexName + "_" + version;
    }

    private String query(final JsonNode queryNode) {
        String query = queryTemplate(queryNode.get("template").asText());
        for (final Iterator<String> iterator = queryNode.get("placeholders").fieldNames(); iterator.hasNext();) {
            final String name = iterator.next();
            query = query.replace(name, queryNode.get("placeholders").get(name).asText());
        }
        return query;
    }
}