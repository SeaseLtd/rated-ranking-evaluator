package io.sease.rre.core;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.Func;
import io.sease.rre.core.domain.*;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;

import java.io.File;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

import static io.sease.rre.Field.*;
import static io.sease.rre.Func.*;
import static java.util.Arrays.stream;
import static java.util.Objects.requireNonNull;
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

    private final SearchPlatform platform;
    private final String [] fields;

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
            final String [] fields) {
        this.configurationsFolder = new File(configurationsFolderPath);
        this.corporaFolder = new File(corporaFolderPath);
        this.ratingsFolder = new File(ratingsFolderPath);
        this.templatesFolder = new File(templatesFolderPath);
        this.platform = platform;
        this.fields = safe(fields);

        this.availableMetricsDefs =
                metrics.stream()
                        .map(Func::newMetricDefinition)
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
        final List<Query> queries = new ArrayList<>();

        ratings().forEach(ratingsNode -> {
            final String indexName = ratingsNode.get(INDEX_NAME).asText();
            final String idFieldName = ratingsNode.get(ID_FIELD_NAME).asText(DEFAULT_ID_FIELD_NAME);
            final File data = new File(corporaFolder, ratingsNode.get(CORPORA_FILENAME).asText());

            if (!data.canRead()) {
                throw new IllegalArgumentException("Unable to read the corpus file " + data.getAbsolutePath());
            }

            prepareData(indexName, data);

            final Corpus corpus = evaluation.findOrCreate(data.getName(), Corpus::new);
            all(ratingsNode.get(TOPICS))
                    .forEach(topicNode -> {
                        final Topic topic = corpus.findOrCreate(topicNode.get(DESCRIPTION).asText(), Topic::new);
                        all(topicNode.get(QUERY_GROUPS))
                                .forEach(groupNode -> {
                                    final QueryGroup group =
                                            topic.findOrCreate(groupNode.get(NAME).asText(), QueryGroup::new);
                                    all(groupNode.get(QUERIES))
                                            .forEach(queryNode -> {
                                                final String query = query(queryNode);
                                                final JsonNode relevantDocuments = groupNode.get(RELEVANT_DOCUMENTS);

                                                final Query queryEvaluation = group.findOrCreate(query, Query::new);
                                                queryEvaluation.setIdFieldName(idFieldName);
                                                queryEvaluation.setRelevantDocuments(relevantDocuments);

                                                queries.add(queryEvaluation);

                                                queryEvaluation.prepare(availableMetrics(availableMetricsDefs, idFieldName, relevantDocuments, versions));

                                                versions.forEach(version -> {
                                                    final AtomicInteger rank = new AtomicInteger(1);
                                                    final QueryOrSearchResponse response =
                                                            platform.executeQuery(
                                                                    indexFqdn(indexName, version),
                                                                    query,
                                                                    fields,
                                                                    Math.max(10, relevantDocuments.size()));

                                                    queryEvaluation.setTotalHits(response.totalHits(), version);
                                                    response.hits().forEach(hit -> queryEvaluation.collect(hit, rank.getAndIncrement(), version));
                                                });
                                            });
                                });
                    });
        });

        platform.beforeStop();

        queries.forEach(Query::notifyCollectedMetrics);

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
        return stream(
                requireNonNull(ratingsFolder.listFiles(ONLY_JSON_FILES)))
                .map(Func::toJson);
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

    /**
     * Prepares the search platform with the given index name and dataset.
     *
     * @param indexName the index name.
     * @param data the dataset.
     */
    private void prepareData(final String indexName, final File data) {
        final File [] versionFolders = safe(configurationsFolder.listFiles(ONLY_NON_HIDDEN_FILES));
        stream(versionFolders)
                .flatMap(versionFolder -> stream(safe(versionFolder.listFiles(ONLY_NON_HIDDEN_FILES))))
                .filter(folder -> folder.getName().equals(indexName))
                .forEach(folder -> platform.load(data, folder, indexFqdn(indexName, folder.getParentFile().getName())));

        this.versions = stream(versionFolders).map(File::getName).collect(toList());
    }

    /**
     * Returns the FDQN of the target index that will be used.
     * Starting from the index name declared in the configuration, RRE uses an internal naming (which adds the version
     * name) for avoiding conflicts between versions.
     *
     * @param indexName the index name.
     * @param version the current version.
     * @return the FDQN of the target index that will be used.
     */
    private String indexFqdn(final String indexName, final String version) {
        return indexName + "_" + version;
    }

    /**
     * Returns a query (as a string) that will be used for executing a specific evaluation.
     * A query string is the result of replacing all placeholders found in the template.
     *
     * @param queryNode the JSON query node (in ratings configuration).
     * @return a query (as a string) that will be used for executing a specific evaluation.
     */
    private String query(final JsonNode queryNode) {
        String query = queryTemplate(queryNode.get("template").asText());
        for (final Iterator<String> iterator = queryNode.get("placeholders").fieldNames(); iterator.hasNext();) {
            final String name = iterator.next();
            query = query.replace(name, queryNode.get("placeholders").get(name).asText());
        }
        return query;
    }
}