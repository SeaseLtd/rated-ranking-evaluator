package io.sease.rre.persistence.impl;

import io.sease.rre.core.domain.Query;
import io.sease.rre.persistence.PersistenceException;
import io.sease.rre.persistence.PersistenceHandler;
import org.apache.http.HttpHost;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import java.io.IOException;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.LinkedTransferQueue;
import java.util.concurrent.TransferQueue;
import java.util.stream.Collectors;

/**
 * Elasticsearch implementation of the {@link PersistenceHandler}, allowing
 * query results to be written directly to Elasticsearch.
 *
 * This uses a ScheduledThreadExecutor to periodically push the results into
 * Elasticsearch using the BulkRequestProcessor mechanism.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class ElasticsearchPersistenceHandler implements PersistenceHandler {

    private static final Logger LOGGER = LogManager.getLogger(ElasticsearchPersistenceHandler.class);

    static final String BASE_URL_KEY = "baseUrl";
    static final String DEFAULT_HOST = "http://localhost:9200";

    private final TransferQueue<Query> queryQueue = new LinkedTransferQueue<>();

    private String name;

    // Elasticsearch configuration
    private List<String> baseUrls;
    private String index;

    private RestHighLevelClient client;

    @Override
    public void configure(String name, Map<String, Object> configuration) {
        this.name = name;
        // Extract the URL(s) - either a list of a single string
        if (configuration.containsKey(BASE_URL_KEY)) {
            final Object url = configuration.get(BASE_URL_KEY);
            if (url instanceof List) {
                baseUrls = ((List<Object>) url).stream().map(String::valueOf).collect(Collectors.toList());
            } else if (url instanceof String) {
                baseUrls = Collections.singletonList(String.valueOf(url));
            } else {
                LOGGER.warn("Could not extract Elasticsearch host URL(s) from configuration!");
                baseUrls = Collections.emptyList();
            }
        } else {
            LOGGER.info("No base URL set for Elasticsearch - defaulting to " + DEFAULT_HOST);
            baseUrls = Collections.singletonList(DEFAULT_HOST);
        }
        this.index = String.valueOf(configuration.get("index"));
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public void beforeStart() throws PersistenceException {
        try {
            // Convert hosts to HTTP host objects
            final HttpHost[] httpHosts = baseUrls.stream()
                    .map(HttpHost::create)
                    .toArray(HttpHost[]::new);

            // Initialise the client
            client = new RestHighLevelClient(RestClient.builder(httpHosts));
        } catch (final IllegalArgumentException e) {
            throw new PersistenceException(e);
        }
    }

    @Override
    public void start() throws PersistenceException {
        // Make sure the cluster is alive
    }

    @Override
    public void recordQuery(Query q) {

    }

    @Override
    public void beforeStop() {

    }

    @Override
    public void stop() {
        try {
            client.close();
        } catch (final IOException e) {
            LOGGER.error("Caught IOException closing Elasticsearch client :: " + e.getMessage());
        }
    }

    List<String> getBaseUrls() {
        return baseUrls;
    }
}
