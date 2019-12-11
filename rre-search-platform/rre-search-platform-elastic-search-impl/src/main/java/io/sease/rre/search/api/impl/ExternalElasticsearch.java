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

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.search.api.QueryOrSearchResponse;
import org.apache.http.HttpHost;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.ElasticsearchException;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * SearchPlatform implementation for connecting to and reading from an external
 * Elasticsearch instance.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class ExternalElasticsearch extends Elasticsearch {

    private static final Logger LOGGER = LogManager.getLogger(ExternalElasticsearch.class);
    private static final String NAME = "External Elasticsearch";
    static final String SETTINGS_FILE = "index-settings.json";

    private final Map<String, RestHighLevelClient> indexClients = new HashMap<>();
    private final List<RestClient> indexLowLevelClients = new ArrayList<>();

    @Override
    public void beforeStart(Map<String, Object> configuration) {
        // No-op for this implementation
    }

    @Override
    public void start() {
        // No-op for this implementation
    }

    @Override
    public void load(File dataToBeIndexed, File settingsFile, String collection, String version) {
        // Corpus file is not used for this implementation
        ObjectMapper mapper = new ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        try {
            // Load the index settings for this version of the search platform
            IndexSettings settings = mapper.readValue(settingsFile, IndexSettings.class);
            if (indexClients.get(version) == null) {
                RestClient lowLevelClient = initialiseLowLevelClient(settings.getHostUrls());
                indexLowLevelClients.add(lowLevelClient);
                indexClients.put(version, new RestHighLevelClient(lowLevelClient));
            }

        } catch (IOException e) {
            LOGGER.error("Could not read settings from " + settingsFile.getName() + " :: " + e.getMessage());
        }
    }

    private RestClient initialiseLowLevelClient(List<String> hosts) {
        // Convert hosts to HTTP host objects
        HttpHost[] httpHosts = hosts.stream()
                .map(HttpHost::create)
                .toArray(HttpHost[]::new);

        return RestClient.builder(httpHosts).build();
    }

    @Override
    public QueryOrSearchResponse executeQuery(final String collection, String version, final String query, final String[] fields, final int maxRows) {

        try {
            final SearchRequest request = buildSearchRequest(collection, query, fields, maxRows);
            final SearchResponse response = runQuery(version, request);
            return convertResponse(response);
        } catch (final ElasticsearchException e) {
            LOGGER.error("Caught ElasticsearchException :: " + e.getMessage());
            return new QueryOrSearchResponse(0, Collections.emptyList());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private SearchResponse runQuery(final String clientId, final SearchRequest request) throws IOException {
        RestHighLevelClient client = indexClients.get(clientId);
        if (client == null) {
            throw new RuntimeException("No HTTP client found for index " + clientId);
        }
        return client.search(request);
    }

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public boolean isSearchPlatformConfiguration(String indexName, File searchEngineStartupSettings) {
        return searchEngineStartupSettings.isFile() && searchEngineStartupSettings.getName().equals(SETTINGS_FILE);
    }

    @Override
    public boolean isCorporaRequired() {
        return false;
    }

    @Override
    public void close() {
        indexLowLevelClients.forEach(this::closeClient);
    }

    private void closeClient(RestClient client) {
        try {
            client.close();
        } catch (IOException e) {
            LOGGER.error("Caught IOException closing ES HTTP Client :: " + e.getMessage());
        }
    }


    public static class IndexSettings {
        @JsonProperty("hostUrls")
        private final List<String> hostUrls;

        public IndexSettings(@JsonProperty("hostUrls") List<String> hostUrls) {

            this.hostUrls = hostUrls;
        }

        List<String> getHostUrls() {
            return hostUrls;
        }
    }
}
