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

    private final Map<String, IndexSettings> indexSettingsMap = new HashMap<>();
    private final Map<String, RestHighLevelClient> indexClients = new HashMap<>();

    @Override
    public void beforeStart(Map<String, Object> configuration) {
        // No-op for this implementation
    }

    @Override
    public void start() {
        // No-op for this implementation
    }

    @Override
    public void load(File corpus, File settingsFile, String targetIndexName) {
        // Corpus file is not used for this implementation
        ObjectMapper mapper = new ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        try {
            // Load the index settings for this version of the search platform
            IndexSettings settings = mapper.readValue(settingsFile, IndexSettings.class);
            indexSettingsMap.put(targetIndexName, settings);
            indexClients.put(targetIndexName, initialiseClient(settings.getHostUrls()));
        } catch (IOException e) {
            LOGGER.error("Could not read settings from " + settingsFile.getName() + " :: " + e.getMessage());
        }
    }

    private RestHighLevelClient initialiseClient(List<String> hosts) {
        // Convert hosts to HTTP host objects
        HttpHost[] httpHosts = hosts.stream()
                .map(HttpHost::create)
                .toArray(HttpHost[]::new);

        return new RestHighLevelClient(RestClient.builder(httpHosts));
    }

    @Override
    public QueryOrSearchResponse executeQuery(final String indexName, final String query, final String[] fields, final int maxRows) {
        // Find the actual index to search
        if (!indexSettingsMap.containsKey(indexName)) {
            throw new IllegalArgumentException("Cannot find settings for index " + indexName);
        }

        try {
            final SearchRequest request = buildSearchRequest(indexSettingsMap.get(indexName).getIndex(), query, fields, maxRows);
            final SearchResponse response = runQuery(indexName, request);
            return convertResponse(response);
        } catch (final ElasticsearchException e) {
            LOGGER.error("Caught ElasticsearchException :: " + e.getMessage());
            return new QueryOrSearchResponse(0, Collections.emptyList());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private SearchResponse runQuery(final String indexKey, final SearchRequest request) throws IOException {
        RestHighLevelClient client = indexClients.get(indexKey);
        if (client == null) {
            throw new RuntimeException("No HTTP client found for index " + indexKey);
        }
        return client.search(request);
    }

    @Override
    public String getName() {
        return NAME;
    }

    @Override
    public boolean isSearchPlatformFile(String indexName, File file) {
        return file.isFile() && file.getName().equals(SETTINGS_FILE);
    }

    @Override
    public boolean isCorporaRequired() {
        return false;
    }

    @Override
    public void close() {
        indexClients.values().forEach(this::closeClient);
    }

    private void closeClient(RestHighLevelClient client) {
        try {
            client.close();
        } catch (IOException e) {
            LOGGER.error("Caught IOException closing ES HTTP Client :: " + e.getMessage());
        }
    }


    public static class IndexSettings {

        @JsonProperty("index")
        private final String index;
        @JsonProperty("hostUrls")
        private final List<String> hostUrls;

        public IndexSettings(@JsonProperty("index") String index,
                             @JsonProperty("hostUrls") List<String> hostUrls) {
            this.index = index;
            this.hostUrls = hostUrls;
        }

        String getIndex() {
            return index;
        }

        List<String> getHostUrls() {
            return hostUrls;
        }
    }
}
