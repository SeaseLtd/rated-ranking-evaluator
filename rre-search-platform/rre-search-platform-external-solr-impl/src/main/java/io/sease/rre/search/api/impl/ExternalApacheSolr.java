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
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import org.apache.solr.client.solrj.SolrClient;
import org.apache.solr.client.solrj.SolrQuery;
import org.apache.solr.client.solrj.SolrRequest;
import org.apache.solr.client.solrj.SolrServerException;
import org.apache.solr.client.solrj.response.SolrPingResponse;
import org.apache.solr.common.SolrException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static java.util.Optional.of;

/**
 * Implementation of the {@link SearchPlatform} interface for external Solr
 * instances.
 * <p>
 * This implementation assumes that the cores (or collections) have been
 * prepared and are ready to use - the cores are not created each run, and the
 * corpus is not loaded to them.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class ExternalApacheSolr implements SearchPlatform {

    private final static Logger LOGGER = LoggerFactory.getLogger(ExternalApacheSolr.class);

    private static final String NAME = "External Apache Solr";
    static final String SETTINGS_FILE = "solr-settings.json";

    private final SolrClientManager clientManager = new SolrClientManager();
    private final Map<String, SolrSettings> settingsMap = new HashMap<>();

    @Override
    public void beforeStart(Map<String, Object> configuration) {
        // No-op for this implementation
    }

    @Override
    public void start() {
        // No-op for this implementation
    }

    @Override
    public void afterStart() {
        // No-op for this implementation
    }

    @Override
    public void load(File dataToBeIndexed, File settingsFile, String collection, String version) {
        // Corpus file is not used for this implementation
        ObjectMapper mapper = new ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        try {
            // Load the index settings for this version of the search platform
            SolrSettings settings = mapper.readValue(settingsFile, SolrSettings.class);
            settingsMap.put(getFullyQualifiedDomainName(collection, version), settings);

            if (clientManager.getSolrClient(version) == null) {
                clientManager.buildSolrClient(version, settings);
            }
        } catch (IOException e) {
            LOGGER.error("Could not read settings from " + settingsFile.getName() + " :: " + e.getMessage());
        }
    }

    @Override
    public void beforeStop() {

    }

    @Override
    public QueryOrSearchResponse executeQuery(String collection, String version, String queryString, String[] fields, int maxRows) {
        try {
            final SolrQuery query =
                    new SolrQuery()
                            .setRows(maxRows)
                            .setFields(fields);
            final ObjectMapper mapper = new ObjectMapper();
            final JsonNode queryDef = mapper.readTree(queryString);

            for (final Iterator<Map.Entry<String, JsonNode>> iterator = queryDef.fields(); iterator.hasNext(); ) {
                final Map.Entry<String, JsonNode> field = iterator.next();
                final String value;
                if (field.getValue().isValueNode()) {
                    value = field.getValue().asText();
                } else {
                    // Either an array or an object - use writeValueAsString() instead
                    // to convert to a string. Useful for writing JSON queries without escaping them.
                    value = mapper.writeValueAsString(field.getValue());
                }
                query.add(field.getKey(), value);
            }

            return of(clientManager.getSolrClient(version)
                    .query(resolveCollectionName(collection, version), query, SolrRequest.METHOD.POST))
                    .map(response ->
                            new QueryOrSearchResponse(
                                    response.getResults().getNumFound(),
                                    new ArrayList<>(response.getResults())))
                    .get();
        } catch (SolrException e) {
            LOGGER.error("Caught Solr exception :: " + e.getMessage());
            return new QueryOrSearchResponse(e.getMessage());
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public boolean isRefreshRequired() {
        return false;
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
        clientManager.close();
    }

    @Override
    public boolean checkCollection(String collection, String version) {
        try {
            SolrClient client = clientManager.getSolrClient(version);
            if (client != null) {
                SolrPingResponse response = client.ping(resolveCollectionName(collection, version));
                return response.getStatus() == 0;
            }
        } catch (SolrException e) {
            // If index doesn't exist, we'll get a SolrException (a RuntimeException)
            LOGGER.warn("Caught SolrException checking for collection {} version {}: {}",
                    collection, version, e.getMessage());
        } catch (SolrServerException | IOException e) {
            LOGGER.warn("Caught exception checking platform for collection {} version {}: {}",
                    collection, version, e.getMessage());
        }
        return false;
    }

    private String resolveCollectionName(String defaultCollection, String version) {
        return Optional.ofNullable(settingsMap.get(getFullyQualifiedDomainName(defaultCollection, version)).getCollectionName())
                .orElse(defaultCollection);
    }

    public static class SolrSettings {

        @JsonProperty("baseUrls")
        private final List<String> baseUrls;
        @JsonProperty("collectionName")
        private final String collectionName;
        @JsonProperty("zkHosts")
        private final List<String> zkHosts;
        @JsonProperty("zkChroot")
        private final String zkChroot;
        @JsonProperty("connectionTimeoutMillis")
        private final Integer connectionTimeout;
        @JsonProperty("socketTimeoutMillis")
        private final Integer socketTimeout;

        public SolrSettings(@JsonProperty("baseUrls") List<String> baseUrls,
                            @JsonProperty("collectionName") String collectionName,
                            @JsonProperty("zkHosts") List<String> zkHosts,
                            @JsonProperty("zkChroot") String zkChroot,
                            @JsonProperty("connectionTimeoutMillis") Integer connectionTimeout,
                            @JsonProperty("socketTimeoutMillis") Integer socketTimeout) throws IllegalArgumentException {
            this.baseUrls = baseUrls;
            this.collectionName = collectionName;
            this.zkHosts = zkHosts;
            this.zkChroot = (zkChroot != null && zkChroot.length() > 0 ? zkChroot : null);
            this.connectionTimeout = connectionTimeout;
            this.socketTimeout = socketTimeout;

            // Check that the required properties are set
            validate();
        }

        private void validate() throws IllegalArgumentException {
            if ((baseUrls == null || baseUrls.isEmpty()) && !hasZookeeperSettings()) {
                throw new IllegalArgumentException("Required configuration missing! No Solr or Zookeeper URLs set!");
            }
        }

        public List<String> getBaseUrls() {
            return baseUrls;
        }

        public String getCollectionName() {
            return collectionName;
        }

        public List<String> getZkHosts() {
            return zkHosts;
        }

        public Optional<String> getZkChroot() {
            return Optional.ofNullable(zkChroot);
        }

        public boolean hasZookeeperSettings() {
            return zkHosts != null && !zkHosts.isEmpty();
        }

        public Integer getConnectionTimeout() {
            return connectionTimeout;
        }

        public Integer getSocketTimeout() {
            return socketTimeout;
        }
    }
}
