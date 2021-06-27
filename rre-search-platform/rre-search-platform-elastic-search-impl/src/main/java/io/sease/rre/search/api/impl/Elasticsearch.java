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
package io.sease.rre.search.api.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.DirectoryUtils;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import io.sease.rre.search.api.UnableToLoadDataException;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.ElasticsearchException;
import org.elasticsearch.action.admin.indices.create.CreateIndexRequest;
import org.elasticsearch.action.bulk.BulkRequest;
import org.elasticsearch.action.bulk.BulkResponse;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.action.support.WriteRequest;
import org.elasticsearch.analysis.common.CommonAnalysisPlugin;
import org.elasticsearch.client.Client;
import org.elasticsearch.common.settings.Settings;
import org.elasticsearch.common.xcontent.XContentType;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.node.Node;
import org.elasticsearch.plugins.Plugin;
import org.elasticsearch.search.builder.SearchSourceBuilder;
import org.elasticsearch.transport.Netty4Plugin;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static java.util.Arrays.asList;
import static java.util.Arrays.stream;
import static java.util.Collections.emptyList;
import static java.util.Collections.emptyMap;
import static java.util.Optional.ofNullable;
import static java.util.stream.Collectors.toList;
import static org.elasticsearch.client.Requests.createIndexRequest;
import static org.elasticsearch.client.Requests.deleteIndexRequest;
import static org.elasticsearch.client.Requests.indicesExistsRequest;
import static org.elasticsearch.node.InternalSettingsPreparer.prepareEnvironment;

/**
 * Elasticsearch platform API implementation.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Elasticsearch implements SearchPlatform {
    private static final Logger LOGGER = LogManager.getLogger(Elasticsearch.class);

    private static class RRENode extends Node {
        RRENode(final Settings settings, final Collection<Class<? extends Plugin>> plugins) {
            super(prepareEnvironment(settings, emptyMap(), null, () -> "ANodeName"), plugins, true);
        }
    }

    private Client proxy;
    private Node elasticsearch;
    private final ObjectMapper mapper = new ObjectMapper();

    private File nodeConfigFolder;
    private boolean mustRefresh = false;

    @Override
    public void beforeStart(final Map<String, Object> configuration) {
        final File logsFolder = new File("target/elasticsearch/logs");
        final File dataFolder = new File((String) configuration.get("path.data"));

        logsFolder.delete();
        logsFolder.mkdirs();

        if ((Boolean) configuration.get("forceRefresh") && dataFolder.exists()) {
            try {
                DirectoryUtils.deleteDirectory(dataFolder);
            } catch (IOException e) {
                LOGGER.error("Could not delete data directory - expect data to be stale!", e);
            }
            dataFolder.delete();
        }
        if (!dataFolder.exists()) {
            dataFolder.mkdirs();
            mustRefresh = true;
        }

        nodeConfigFolder = new File((String) configuration.get("path.home"), "config");
        nodeConfigFolder.mkdirs();

        final Settings.Builder settings = Settings.builder()
                .put("path.home", (String) configuration.get("path.home"))
                .put("transport.type", "netty4")
                .put("http.type", "netty4")
                .put("network.host", "127.0.0.1")
                .put("http.port", (Integer) configuration.getOrDefault("network.host", 9200))
                .put("path.logs", logsFolder.getAbsolutePath())
                .put("path.data", dataFolder.getAbsolutePath())
                .put("cluster.name", "rre_" + System.currentTimeMillis());
        elasticsearch = new RRENode(settings.build(), plugins(configuration));
    }

    @Override
    public void load(final File dataToBeIndexed, File indexShapeFile, String collection, String version) {
        if (!indexShapeFile.getName().startsWith("index")) {
            throw new IllegalArgumentException("Unable to find an index-shape (i.e. settings + mappings) within the configuration folder.");
        }
        String indexName = getFullyQualifiedDomainName(collection, version);
        try {
            final ObjectMapper mapper = new ObjectMapper();
            final JsonNode esconfig = mapper.readTree(indexShapeFile);

            if (proxy.admin().indices().exists(indicesExistsRequest(indexName)).actionGet().isExists()) {
                proxy.admin().indices().delete(deleteIndexRequest(indexName)).actionGet();
            }

            List<JsonNode> protectedKeywordsPaths = esconfig.findParents("keywords_path");
            List<JsonNode> synonymsPaths = esconfig.findParents("synonyms_path");
            List<JsonNode> stopwordsPaths = esconfig.findParents("stopwords_path");

            final File configurationFolder = indexShapeFile.getParentFile();
            final String namespace = configurationFolder.getName();

            insertNamespaces(protectedKeywordsPaths, "keywords_path", configurationFolder, namespace);
            insertNamespaces(synonymsPaths, "synonyms_path", configurationFolder, namespace);
            insertNamespaces(stopwordsPaths, "stopwords_path", configurationFolder, namespace);

            final CreateIndexRequest request = createIndexRequest(indexName);
            ofNullable(esconfig.get("settings"))
                    .ifPresent(settings -> {
                        try {
                            request.settings(Settings.builder().loadFromSource(mapper.writeValueAsString(settings), XContentType.JSON).build());
                        } catch (JsonProcessingException exception) {
                            LOGGER.error("Invalid \"settings\" section in Elasticsearch configuration. " +
                                    "As consequence of that the entire section will be skipped.", exception);
                        }
                    });

            ofNullable(esconfig.get("mappings"))
                    .ifPresent(mappings -> {
                        try {
                            request.mapping("doc", mapper.writeValueAsString(mappings), XContentType.JSON);
                        } catch (JsonProcessingException exception) {
                            LOGGER.error("Invalid \"mappings\" section in Elasticsearch configuration. " +
                                    "As consequence of that the entire section will be skipped.", exception);
                        }
                    });

            proxy.admin().indices().create(request).actionGet();

            final BulkRequest bulkRequest = new BulkRequest();
            final List<String> lines = Files.readAllLines(dataToBeIndexed.toPath());

            for (int i = 0; i < lines.size(); i += 2) {
                JsonNode metadata = mapper.readTree(lines.get(i)).get("index");
                String document = lines.get(i + 1);
                bulkRequest.add(
                        new IndexRequest(indexName)
                                .type(metadata.get("_type").asText())
                                .id(metadata.get("_id").asText())
                                .source(document, XContentType.JSON)).setRefreshPolicy(WriteRequest.RefreshPolicy.IMMEDIATE);
            }

            final BulkResponse response = proxy.bulk(bulkRequest).actionGet();
            if (response.hasFailures()) {
                final String message =
                        "Unable to load datafile (" +
                                dataToBeIndexed.getAbsolutePath() +
                                ") in " +
                                getName() +
                                " using the index shape (" +
                                indexShapeFile.getAbsolutePath() +
                                ") into the index " +
                                indexName +
                                ". Error message is: " +
                                response.buildFailureMessage();
                throw new UnableToLoadDataException(message);
            }
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    @Override
    public String getName() {
        return "Elasticsearch";
    }

    @Override
    public void start() {
        try {
            elasticsearch.start();
            proxy = elasticsearch.client();
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    @Override
    public void afterStart() {
        // Nothing to be done here
    }

    @Override
    public void beforeStop() {
        // TODO: remove everything
    }

    @Override
    public void close() {
        try {
            elasticsearch.close();
            proxy.close();
        } catch (final IOException ignore) {
            // Ignore
        }
    }

    @Override
    public QueryOrSearchResponse executeQuery(final String collection, String version, final String query, final String[] fields, final int maxRows) {
        String indexName = getFullyQualifiedDomainName(collection, version);
        try {
            final SearchResponse qresponse = proxy.search(buildSearchRequest(indexName, query, fields, maxRows)).actionGet();
            return convertResponse(qresponse);
        } catch (final ElasticsearchException e) {
            LOGGER.error("Caught ElasticsearchException :: " + e.getMessage());
            return new QueryOrSearchResponse(e.getMessage());
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    SearchRequest buildSearchRequest(final String indexName, final String query, final String[] fields, final int maxRows) throws IOException {
        final String q = mapper.writeValueAsString(mapper.readTree(query).get("query"));
        final SearchSourceBuilder qBuilder = new SearchSourceBuilder()
                .query(QueryBuilders.wrapperQuery(q))
                .size(maxRows)
                .fetchSource(fields, null);
        return new SearchRequest(indexName).source(qBuilder);
    }

    QueryOrSearchResponse convertResponse(final SearchResponse searchResponse) {
        return new QueryOrSearchResponse(
                searchResponse.getHits().getTotalHits().value,
                stream(searchResponse.getHits().getHits())
                        .map(hit -> {
                            final Map<String, Object> result = new HashMap<>(hit.getSourceAsMap());
                            result.put("_id", hit.getId());
                            return result;
                        })
                        .collect(toList()));
    }

    @Override
    public boolean isRefreshRequired() {
        return mustRefresh;
    }

    @SuppressWarnings("unchecked")
    private List<Class<? extends Plugin>> plugins(final Map<String, Object> configuration) {
        final List<Class<? extends Plugin>> defaultPlugins = asList(Netty4Plugin.class, CommonAnalysisPlugin.class);
        final List<? extends Class<? extends Plugin>> customPlugins =
                ofNullable((List<String>)configuration.get("plugins"))
                        .map(plugins ->
                                plugins.stream()
                                        .map(String::trim)
                                        .filter(v -> !v.isEmpty())
                                        .map(v -> {
                                            try {
                                                return (Class<? extends Plugin>)Class.forName(v, true, Thread.currentThread().getContextClassLoader());
                                            } catch (final Exception exception) {
                                                throw new IllegalArgumentException(exception);
                                            }
                                        })
                                        .collect(toList()))
                        .orElse(emptyList());

        final List<Class<? extends Plugin>> plugins = new ArrayList<>(defaultPlugins);
        plugins.addAll(customPlugins);

        return plugins;
    }

    private void insertNamespaces(final List<JsonNode> parents, final String pathAttributeName, final File configurationFolder, final String namespace) {
        parents.forEach(parentNode -> {
            final String path = parentNode.get(pathAttributeName).asText();
            final File declaredPath = new File(configurationFolder, path);

            final String originalFilename = declaredPath.getName();
            final String namespacedFilename = namespace + "_" + declaredPath.getName();

            final File targetPath = new File(nodeConfigFolder, namespacedFilename);

            try {
                Files.copy(declaredPath.toPath(), targetPath.toPath(), StandardCopyOption.REPLACE_EXISTING);
                ((ObjectNode)parentNode).put(pathAttributeName, path.replace(originalFilename, namespacedFilename));
            } catch (IOException exception) {
                throw new RuntimeException("Unable to deal with configuration file " + declaredPath.getAbsolutePath() + ". Target path was " + targetPath.getAbsolutePath());
            }
        });
    }

    @Override
    public boolean isSearchPlatformConfiguration(String indexName, File file) {
        return file.isFile() && file.getName().equals("index-shape.json");
    }

    @Override
    public boolean isCorporaRequired() {
        return true;
    }

    @Override
    public boolean checkCollection(String collection, String version) {
        return proxy.admin().indices().exists(indicesExistsRequest(getFullyQualifiedDomainName(collection, version))).actionGet().isExists();
    }
}
