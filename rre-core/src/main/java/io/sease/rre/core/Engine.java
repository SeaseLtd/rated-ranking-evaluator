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
package io.sease.rre.core;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.Field;
import io.sease.rre.Func;
import io.sease.rre.core.domain.Corpus;
import io.sease.rre.core.domain.Evaluation;
import io.sease.rre.core.domain.Query;
import io.sease.rre.core.domain.QueryGroup;
import io.sease.rre.core.domain.Topic;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.MetricClassManager;
import io.sease.rre.core.evaluation.EvaluationConfiguration;
import io.sease.rre.core.evaluation.EvaluationManager;
import io.sease.rre.core.evaluation.EvaluationManagerFactory;
import io.sease.rre.core.template.impl.CachingQueryTemplateManager;
import io.sease.rre.core.version.VersionManager;
import io.sease.rre.core.version.VersionManagerImpl;
import io.sease.rre.persistence.PersistenceConfiguration;
import io.sease.rre.persistence.PersistenceHandler;
import io.sease.rre.persistence.PersistenceManager;
import io.sease.rre.search.api.SearchPlatform;
import io.sease.rre.search.api.SearchPlatformException;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import static io.sease.rre.Field.CORPORA_FILENAME;
import static io.sease.rre.Field.DEFAULT_ID_FIELD_NAME;
import static io.sease.rre.Field.DESCRIPTION;
import static io.sease.rre.Field.ID_FIELD_NAME;
import static io.sease.rre.Field.INDEX_NAME;
import static io.sease.rre.Field.NAME;
import static io.sease.rre.Field.QUERIES;
import static io.sease.rre.Field.QUERY_GROUPS;
import static io.sease.rre.Field.RELEVANT_DOCUMENTS;
import static io.sease.rre.Field.TOPICS;
import static io.sease.rre.Field.UNNAMED;
import static io.sease.rre.Func.ONLY_JSON_FILES;
import static io.sease.rre.Func.ONLY_NON_HIDDEN_FILES;
import static io.sease.rre.Func.safe;
import static java.util.Arrays.stream;
import static java.util.Objects.requireNonNull;
import static java.util.Optional.ofNullable;
import static java.util.stream.Collectors.toList;

/**
 * RRE core engine.
 * The engine is responsible for the whole evaluation process execution.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Engine {
    private final static Logger LOGGER = LogManager.getLogger(Engine.class);

    private final File corporaFolder;
    private final File ratingsFolder;

    private final MetricClassManager metricClassManager;

    private final SearchPlatform platform;

    private FileUpdateChecker fileUpdateChecker;

    private final ObjectMapper mapper = new ObjectMapper();

    private final PersistenceManager persistenceManager;

    private final VersionManager versionManager;
    private final EvaluationManager evaluationManager;

    private Integer minimumRequiredResults = null;

    /**
     * Builds a new {@link Engine} instance with the given data.
     *
     * @param platform                 the search platform in use.
     * @param configurationsFolderPath the configurations folder path.
     * @param corporaFolderPath        the corpora folder path.
     * @param ratingsFolderPath        the ratings folder path.
     * @param templatesFolderPath      the query templates folder path.
     * @param metricClassManager       the manager class for the metrics being evaluated.
     * @param fields                   the fields to retrieve with each result.
     * @param exclude                  a list of folders to exclude when scanning the configuration folders.
     * @param include                  a list of folders to include from the configuration folders.
     * @param checksumFilepath         the path to the file used to store the configuration checksums.
     * @param persistenceConfiguration the persistence framework configuration.
     * @param evaluationConfiguration  the evaluation manager configuration.
     */
    public Engine(
            final SearchPlatform platform,
            final String configurationsFolderPath,
            final String corporaFolderPath,
            final String ratingsFolderPath,
            final String templatesFolderPath,
            final MetricClassManager metricClassManager,
            final String[] fields,
            final List<String> exclude,
            final List<String> include,
            final String checksumFilepath,
            final PersistenceConfiguration persistenceConfiguration,
            final EvaluationConfiguration evaluationConfiguration) {
        this.corporaFolder = corporaFolderPath == null ? null : new File(corporaFolderPath);
        this.ratingsFolder = new File(ratingsFolderPath);
        this.platform = platform;

        this.metricClassManager = metricClassManager;

        this.persistenceManager = new PersistenceManager();
        initialisePersistenceManager(persistenceConfiguration);

        this.versionManager = new VersionManagerImpl(new File(configurationsFolderPath), include, exclude, persistenceConfiguration.isUseTimestampAsVersion());
        this.evaluationManager = EvaluationManagerFactory.instantiateEvaluationManager(
                evaluationConfiguration,
                platform,
                persistenceManager,
                new CachingQueryTemplateManager(templatesFolderPath),
                safe(fields),
                versionManager.getConfigurationVersions(),
                versionManager.getVersionTimestamp());

        initialiseFileUpdateChecker(checksumFilepath);
    }

    /**
     * Fully parameterised constructor, does no initialisation apart from
     * setting up the checksum file, if required.
     *
     * @param platform           the search platform.
     * @param corporaFolder      the folder holding the corpora data (optional).
     * @param ratingsFolder      the folder holding the ratings details.
     * @param checksumFile       the path to the checksum file (optional).
     * @param metricClassManager a fully initialised metric class manager.
     * @param persistenceManager a fully initialised persistence manager.
     * @param versionManager     a fully initialised version manager.
     * @param evaluationManager  a fully initialised evaluation manager.
     */
    public Engine(
            final SearchPlatform platform,
            final File corporaFolder,
            final File ratingsFolder,
            final String checksumFile,
            final MetricClassManager metricClassManager,
            final PersistenceManager persistenceManager,
            final VersionManager versionManager,
            final EvaluationManager evaluationManager) {
        this.platform = platform;
        this.corporaFolder = corporaFolder;
        this.ratingsFolder = ratingsFolder;
        this.metricClassManager = metricClassManager;
        this.persistenceManager = persistenceManager;
        this.versionManager = versionManager;
        this.evaluationManager = evaluationManager;
        initialiseFileUpdateChecker(checksumFile);
    }

    private void initialiseFileUpdateChecker(String checksumFile) {
        if (checksumFile != null) {
            try {
                fileUpdateChecker = new FileUpdateChecker(checksumFile);
            } catch (IOException e) {
                LOGGER.warn("Could not create file update checker: " + e.getMessage());
                fileUpdateChecker = null;
            }
        } else {
            fileUpdateChecker = null;
        }
    }

    public String name(final JsonNode node) {
        return ofNullable(
                ofNullable(node.get(DESCRIPTION)).orElse(node.get(NAME)))
                .map(JsonNode::asText)
                .orElse(UNNAMED);
    }

    private void initialisePersistenceManager(final PersistenceConfiguration persistenceConfiguration) {
        persistenceConfiguration.getHandlers().forEach((n, h) -> {
            try {
                // Instantiate the handler
                PersistenceHandler handler = (PersistenceHandler) Class.forName(h).newInstance();
                handler.configure(n, persistenceConfiguration.getHandlerConfigurationByName(n));
                persistenceManager.registerHandler(handler);
            } catch (ClassNotFoundException | InstantiationException | IllegalAccessException e) {
                LOGGER.error("[" + n + "] Caught exception instantiating persistence handler :: " + e.getMessage(), e);
            }
        });
    }

    /**
     * Executes the evaluation process.
     *
     * @param configuration the engine configuration.
     * @return the evaluation result.
     */
    public Evaluation evaluate(final Map<String, Object> configuration) {
        try {
            LOGGER.info("RRE: New evaluation session is starting...");

            platform.beforeStart(configuration);
            persistenceManager.beforeStart();

            LOGGER.info("RRE: Search Platform in use: " + platform.getName());
            LOGGER.info("RRE: Starting " + platform.getName() + "...");

            platform.start();
            persistenceManager.start();

            LOGGER.info("RRE: " + platform.getName() + " Search Platform successfully started.");

            platform.afterStart();

            final Evaluation evaluation = new Evaluation();

            // Start the evaluation process for all of the ratings nodes
            ratings().forEach(ratingsNode -> evaluateRatings(evaluation, ratingsNode));

            // Wait for the evaluations to complete
            while (evaluationManager.isRunning()) {
                LOGGER.info("  ... completed {} / {} evaluations ...",
                        (evaluationManager.getTotalQueries() - evaluationManager.getQueriesRemaining()),
                        evaluationManager.getTotalQueries());
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException ignore) {
                }
            }

            if (evaluationManager.getTotalQueries() > 0) {
                LOGGER.info("  ... completed all {} evaluations.", evaluationManager.getTotalQueries());
            } else {
                LOGGER.warn("  ... no queries evaluated!");
            }

            return evaluation;
        } finally {
            LOGGER.info("RRE: " + platform.getName() + " Evaluation complete - preparing for shutdown");
            platform.beforeStop();
            persistenceManager.beforeStop();
            LOGGER.info("RRE: " + platform.getName() + " Search Platform shutdown procedure executed.");
            LOGGER.info("RRE: Stopping persistence manager");
            persistenceManager.stop();
        }
    }

    /**
     * Evaluate a single ratings set, updating the evaluation with the results.
     *
     * @param evaluation  the evaluation holding the query results.
     * @param ratingsNode the contents of the ratings set.
     */
    private void evaluateRatings(Evaluation evaluation, JsonNode ratingsNode) {
        LOGGER.info("RRE: Ratings Set processing starts");

        final String indexName =
                requireNonNull(
                        ratingsNode.get(INDEX_NAME),
                        "WARNING!!! \"" + INDEX_NAME + "\" attribute not found!").asText();
        final String idFieldName =
                requireNonNull(
                        ratingsNode.get(ID_FIELD_NAME),
                        "WARNING!!! \"" + ID_FIELD_NAME + "\" attribute not found!")
                        .asText(DEFAULT_ID_FIELD_NAME);

        final Optional<File> data = data(ratingsNode);
        final String queryPlaceholder = ofNullable(ratingsNode.get("query_placeholder")).map(JsonNode::asText).orElse("$query");

        LOGGER.info("");
        LOGGER.info("*********************************");
        LOGGER.info("RRE: Index name => " + indexName);
        LOGGER.info("RRE: ID Field name => " + idFieldName);
        data.ifPresent(file -> LOGGER.info("RRE: Test Collection => " + file.getAbsolutePath()));

        try {
            // Load the data. If the collection being loaded cannot be reached,
            // this will fail.
            prepareData(indexName, data.orElse(null));

            final Corpus corpus = evaluation.findOrCreate(data.map(File::getName).orElse(indexName), Corpus::new);
            all(ratingsNode, TOPICS)
                    .forEach(topicNode -> {
                        final Topic topic = corpus.findOrCreate(name(topicNode), Topic::new);

                        LOGGER.info("TOPIC: " + topic.getName());

                        all(topicNode, QUERY_GROUPS)
                                .forEach(groupNode -> {
                                    final QueryGroup group = topic.findOrCreate(name(groupNode), QueryGroup::new);

                                    LOGGER.info("\tQUERY GROUP: " + group.getName());

                                    final String sharedTemplate = ofNullable(groupNode.get("template")).map(JsonNode::asText).orElse(null);
                                    all(groupNode, QUERIES)
                                            .forEach(queryNode -> {
                                                final String queryString = queryNode.findValue(queryPlaceholder).asText();

                                                LOGGER.info("\t\tQUERY: " + queryString);

                                                final JsonNode relevantDocuments = relevantDocuments(
                                                        Optional.ofNullable(queryNode.get(RELEVANT_DOCUMENTS))
                                                                .orElse(groupNode.get(RELEVANT_DOCUMENTS)));
                                                final Query queryEvaluation = group.findOrCreate(queryString, Query::new);
                                                queryEvaluation.setIdFieldName(idFieldName);
                                                queryEvaluation.setRelevantDocuments(relevantDocuments);

                                                List<Metric> metrics = availableMetrics(idFieldName, relevantDocuments,
                                                        new ArrayList<>(versionManager.getConfigurationVersions()));
                                                queryEvaluation.prepare(metrics);

                                                evaluationManager.evaluateQuery(queryEvaluation, indexName, queryNode, sharedTemplate,
                                                        Math.max(relevantDocuments.size(), minimumRequiredResults(metrics)));
                                            });
                                });
                    });
        } catch (SearchPlatformException spe) {
            LOGGER.error("SearchPlatform error while evaluating ratings: {}", spe.getMessage());
        }
    }

    private Optional<File> data(final JsonNode ratingsNode) {
        final File retFile;

        if (platform.isCorporaRequired()) {
            final File corporaFile =
                    new File(
                            corporaFolder,
                            requireNonNull(
                                    ratingsNode.get(CORPORA_FILENAME),
                                    "WARNING!!! \"" + CORPORA_FILENAME + "\" attribute not found!").asText());

            if (corporaFile.getName().endsWith(".zip")) {
                retFile = unzipAndGet(corporaFile);
            } else {
                retFile = corporaFile;
            }

            if (!retFile.canRead()) {
                throw new IllegalArgumentException("RRE: WARNING!!! Unable to read the corpus file " + retFile.getAbsolutePath());
            }
        } else {
            retFile = null;
        }

        return Optional.ofNullable(retFile);
    }

    private File unzipAndGet(final File corporaFile) {
        LOGGER.info("RRE: found a compressed corpora file: " + corporaFile.getAbsolutePath());

        final File outputFolder = new File(System.getProperty("java.io.tmpdir"));

        LOGGER.info("RRE: uncompressing corpora file under: " + outputFolder.getAbsolutePath());

        try (final ZipInputStream zInputStream = new ZipInputStream(new FileInputStream((corporaFile)))) {
            ZipEntry entry = zInputStream.getNextEntry();
            while (entry != null) {
                if (entry.getName().endsWith(".json")) {
                    LOGGER.info("RRE: found a corpora candidate within the archive: " + entry.getName());

                    final File outputFile = new File(outputFolder, entry.getName());
                    try (final BufferedOutputStream bos = new BufferedOutputStream(new FileOutputStream(outputFile))) {
                        final byte[] buffer = new byte[1024];
                        int read;
                        while ((read = zInputStream.read(buffer)) != -1) {
                            bos.write(buffer, 0, read);
                        }
                        return outputFile;
                    }
                }

                zInputStream.closeEntry();
                entry = zInputStream.getNextEntry();
            }
            throw new IllegalArgumentException("Unable to find a valid dataset within the compressed corpora file: " + corporaFile.getAbsolutePath());
        } catch (final IOException exception) {
            throw new IllegalArgumentException("Unable to read the compressed corpora file: " + corporaFile.getAbsolutePath());
        }
    }

    /**
     * Creates the object representation of relevant documents (i.e judgements).
     *
     * @param relevantDocumentsDefiniton the relevant documents definition as found in the ratings.json
     * @return the object representation of relevant documents (i.e judgements).
     */
    public JsonNode relevantDocuments(final JsonNode relevantDocumentsDefiniton) {
        if (relevantDocumentsDefiniton == null) return mapper.createArrayNode();
        if (relevantDocumentsDefiniton.size() == 0) return relevantDocumentsDefiniton;

        final boolean gainToArrayMode = relevantDocumentsDefiniton.fields().next().getValue().isArray();
        if (gainToArrayMode) {
            final ObjectNode relevantDocumentsContainer = mapper.createObjectNode();
            relevantDocumentsDefiniton.fields()
                    .forEachRemaining(entry -> {
                        final int gain = Integer.parseInt(entry.getKey());
                        entry.getValue().iterator().forEachRemaining(node -> {
                            final ObjectNode doc = mapper.createObjectNode();
                            doc.put(Field.GAIN, gain);
                            relevantDocumentsContainer.replace(node.asText(), doc);
                        });
                    });
            return relevantDocumentsContainer;
        } else {
            return relevantDocumentsDefiniton;
        }
    }

    /**
     * Creates a new set of metrics.
     *
     * @param idFieldName          the id fieldname.
     * @param relevantDocumentsMap the relevant documents for a given query.
     * @param versions             the available versions for a given query.
     * @return a new metrics set for the current query evaluation.
     */
    private List<Metric> availableMetrics(
            final String idFieldName,
            final JsonNode relevantDocumentsMap,
            final List<String> versions) {
        return metricClassManager.getMetrics()
                .stream()
                .map(metricName -> {
                    try {
                        final Metric metric = metricClassManager.instantiateMetric(metricName);
                        metric.setIdFieldName(idFieldName);
                        metric.setRelevantDocuments(relevantDocumentsMap);
                        metric.setVersions(versions);
                        return metric;
                    } catch (final Exception exception) {
                        throw new IllegalArgumentException(exception);
                    }
                }).collect(toList());
    }

    private int minimumRequiredResults(List<Metric> metrics) {
        if (minimumRequiredResults == null) {
            minimumRequiredResults = metrics.stream().map(Metric::getRequiredResults).max(Integer::compareTo).orElse(Metric.DEFAULT_REQUIRED_RESULTS);
        }
        return minimumRequiredResults;
    }

    /**
     * Loads the ratings associated with the given name.
     *
     * @return the ratings / judgements for this evaluation suite.
     */
    private Stream<JsonNode> ratings() {
        final File[] ratingsFiles =
                requireNonNull(
                        ratingsFolder.listFiles(ONLY_JSON_FILES),
                        "Unable to find the ratings folder.");

        LOGGER.info("RRE: found " + ratingsFiles.length + " ratings sets.");

        return stream(ratingsFiles).map(Func::toJson);
    }

    /**
     * Streams out all members of a given JSON node.
     *
     * @param source the parent JSON node.
     * @return a stream consisting of all children of the given JSON node.
     */
    private Stream<JsonNode> all(final JsonNode source, final String name) {
        return ofNullable(source.get(name))
                .map(node -> StreamSupport.stream(node.spliterator(), false))
                .orElseGet(() -> Stream.of(source));
    }

    /**
     * Prepares the search platform with the given index name and dataset.
     *
     * @param collection      the index name.
     * @param dataToBeIndexed the dataset.
     * @throws SearchPlatformException if problems occur loading data to the
     *                                 search platform.
     */
    private void prepareData(final String collection, final File dataToBeIndexed) throws SearchPlatformException {
        if (dataToBeIndexed != null) {
            LOGGER.info("Preparing dataToBeIndexed for " + collection + " from " + dataToBeIndexed.getAbsolutePath());
        } else {
            LOGGER.info("Preparing platform for " + collection);
        }

        Collection<File> configFiles = versionManager.getConfigurationVersionFolders().stream()
                .filter(this::isConfigurationReloadNecessary)
                .flatMap(versionFolder -> stream(safe(versionFolder.listFiles(ONLY_NON_HIDDEN_FILES))))
                .filter(file -> platform.isSearchPlatformConfiguration(collection, file))
                .sorted()
                .collect(Collectors.toList());
        for (File searchPlatformConfiguration : configFiles) {
            LOGGER.info("RRE: Loading the Search Engine " + platform.getName() + ", configuration version " + searchPlatformConfiguration.getParentFile().getName());
            String version = searchPlatformConfiguration.getParentFile().getName();
            platform.load(dataToBeIndexed, searchPlatformConfiguration, collection, version);
            if (!platform.checkCollection(collection, version)) {
                throw new SearchPlatformException("Collection check failed for " + collection + " version " + version);
            }
        }

        LOGGER.info("RRE: " + platform.getName() + " has been correctly loaded.");

        flushFileChecksums();

        LOGGER.info("RRE: target versions are " + String.join(",", versionManager.getConfigurationVersions()));
    }

    private boolean isConfigurationReloadNecessary(File versionFolder) {
        boolean corporaChanged = folderHasChanged(corporaFolder);
        return folderHasChanged(versionFolder) || corporaChanged || platform.isRefreshRequired();
    }

    private boolean folderHasChanged(File folder) {
        boolean ret = true;

        if (fileUpdateChecker != null) {
            try {
                ret = fileUpdateChecker.directoryHasChanged(folder.getAbsolutePath());
            } catch (IOException e) {
                LOGGER.warn("Could not check file update status for " + folder + " :: " + e.getMessage());
            }
        }

        return ret;
    }

    private void flushFileChecksums() {
        if (fileUpdateChecker != null) {
            try {
                fileUpdateChecker.writeChecksums();
            } catch (IOException e) {
                LOGGER.error("Could not write file checksums :: " + e.getMessage());
            }
        }
    }

    
}