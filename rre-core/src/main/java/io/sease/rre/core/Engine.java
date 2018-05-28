package io.sease.rre.core;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.*;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;

import java.io.File;
import java.nio.file.Files;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
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

    private final SearchPlatform platform;

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
            final String templatesFolderPath) {
        this.configurationsFolder = new File(configurationsFolderPath);
        this.corporaFolder = new File(corporaFolderPath);
        this.ratingsFolder = new File(ratingsFolderPath);
        this.templatesFolder = new File(templatesFolderPath);
        this.platform = platform;
    }

    /**
     * Executes the evaluation process.
     *
     * @param configuration the engine configuration.
     * @return the evaluation result.
     */
    @SuppressWarnings("unchecked")
    public Evaluation evaluate(final Map<String, Object> configuration){
        final List<Class<? extends Metric>> availableMetricsDefs =
                ((List<String>)configuration.get("metrics")).stream()
                    .filter(Objects::nonNull)
                    .map(this::newMetricInstance)
                    .collect(toList());

        final JsonNode ratingsNode = ratings();

        platform.beforeStart(configuration);
        platform.start();
        platform.afterStart();

        final String indexName = ratingsNode.get("index").asText();
        final String idFieldName = ratingsNode.get("id_field").asText("id");
        final File data = new File(corporaFolder, ratingsNode.get("corpora_file").asText());
        if (!data.canRead()) {
            throw new IllegalArgumentException("Unable to read the corpus file " + data.getAbsolutePath());
        }

        final Evaluation evaluation = new Evaluation();
        final Corpus corpus = evaluation.findOrCreate(data.getName(), Corpus::new);

        stream(safe(configurationsFolder.listFiles(file -> file.isDirectory() && !file.isHidden())))
                .flatMap(versionFolder -> stream(safe(versionFolder.listFiles(file -> file.isDirectory() && !file.isHidden()))))
                .filter(folder -> folder.getName().equals(indexName))
                .forEach(folder -> {
                    final String version = folder.getParentFile().getName();
                    final String internalIndexName = indexName + "_" + version;

                   // final ConfigurationVersion configurationVersion = corpus.add(new ConfigurationVersion(folder.getParentFile().getName()));
                    platform.load(data, folder, internalIndexName);

                    all(ratingsNode.get("topics"))
                            .forEach(topicNode -> {
                                final Topic topic =
                                        corpus.findOrCreate(topicNode.get("description").asText(), Topic::new);

                                all(topicNode.get("query_groups"))
                                        .forEach(queryGroup -> {
                                            final QueryGroup group = topic.findOrCreate(queryGroup.get("name").asText(), QueryGroup::new);
                                            all(queryGroup.get("queries"))
                                                    .forEach(queryNode -> {
                                                        String query = queryTemplate(queryNode.get("template").asText());
                                                        for (final Iterator<String> iterator = queryNode.get("placeholders").fieldNames(); iterator.hasNext();) {
                                                            final String name = iterator.next();
                                                            query = query.replace(name, queryNode.get("placeholders").get(name).asText());
                                                        }

                                                        final QueryEvaluation queryEvaluation = group.findOrCreate(query, QueryEvaluation::new);
                                                        final ConfigurationVersion configurationVersion = queryEvaluation.findOrCreate(version, ConfigurationVersion::new);

                                                        final QueryOrSearchResponse response = platform.executeQuery(internalIndexName, query);
                                                        final JsonNode relevantDocuments = queryGroup.get("relevant_documents");

                                                        configurationVersion.prepare(availableMetrics(availableMetricsDefs, idFieldName, relevantDocuments, response.totalHits()));
                                                        response.hits().forEach(hit -> configurationVersion.stream().forEach(metric -> metric.collect(hit)));
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
     * @param totalHits the total hits for a given query.
     * @return a new metrics set for the current query evaluation.
     */
    private List<Metric> availableMetrics(
            final List<Class<? extends Metric>> definitions,
            final String idFieldName,
            final JsonNode relevantDocumentsMap,
            final long totalHits) {
        return definitions
                .stream()
                .map(def -> {
                    try {
                        final Metric metric = def.newInstance();
                        metric.setIdFieldName(idFieldName);
                        metric.setRelevantDocuments(relevantDocumentsMap);
                        metric.setTotalHits(totalHits);
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
    private JsonNode ratings() {
        try {
            final ObjectMapper mapper = new ObjectMapper();
            return mapper.readTree(new File(ratingsFolder, "ratings.json"));
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
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
    private Class<? extends Metric> newMetricInstance(final String clazzName) {
        try {
            return (Class<? extends Metric>) Class.forName(clazzName);
        } catch (final Exception exception) {
            throw new IllegalArgumentException(exception);
        }
    }
}