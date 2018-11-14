package io.sease.rre.search.api.impl;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.search.api.QueryOrSearchResponse;
import org.apache.http.HttpHost;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import java.io.File;
import java.io.IOException;
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

    private RestHighLevelClient client;

    private final Map<String, IndexSettings> indexSettingsMap = new HashMap<>();

    @Override
    public void beforeStart(Map<String, Object> configuration) {
        HttpHost[] hosts = ((List<String>) configuration.get("hosts")).stream()
                .map(HttpHost::create)
                .toArray(HttpHost[]::new);

        client = new RestHighLevelClient(RestClient.builder(hosts));
    }

    @Override
    public void start() {
        // No-op for this implementation
    }

    @Override
    public void load(File corpus, File settingsFile, String targetIndexName) {
        ObjectMapper mapper = new ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        try {
            // Load the index settings for this version of the index
            IndexSettings settings = mapper.readValue(settingsFile, IndexSettings.class);
            indexSettingsMap.put(targetIndexName, settings);
        } catch (IOException e) {
            LOGGER.error("Could not read settings from " + settingsFile.getName() + " :: " + e.getMessage());
        }
    }

    @Override
    public QueryOrSearchResponse executeQuery(String indexName, String query, String[] fields, int maxRows) {
        // Find the actual index to search
        if (!indexSettingsMap.containsKey(indexName)) {
            throw new IllegalArgumentException("Cannot find settings for index " + indexName);
        }

        return super.executeQuery(indexSettingsMap.get(indexName).getIndex(), query, fields, maxRows);
    }

    @Override
    protected SearchResponse executeQuery(SearchRequest request) throws IOException {
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
        try {
            client.close();
        } catch (IOException e) {
            LOGGER.error("Caught IOException closing ES HTTP client :: " + e.getMessage());
        }
    }


    public static class IndexSettings {

        @JsonProperty("index")
        private final String index;

        public IndexSettings(@JsonProperty("index") String index) {
            this.index = index;
        }

        public String getIndex() {
            return index;
        }
    }
}
