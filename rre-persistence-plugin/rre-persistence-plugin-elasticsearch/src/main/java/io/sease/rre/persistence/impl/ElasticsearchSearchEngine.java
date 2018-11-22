package io.sease.rre.persistence.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.http.util.EntityUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import java.io.IOException;
import java.util.Map;

/**
 * Elasticsearch search engine, for handling interactions with Elasticsearch
 * directly.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class ElasticsearchSearchEngine {

    private static final Logger LOGGER = LogManager.getLogger(ElasticsearchSearchEngine.class);

    static final String GET_METHOD = "GET";
    static final String CLUSTER_HEALTH_ENDPOINT = "/_cluster/health";

    private final RestHighLevelClient client;

    public ElasticsearchSearchEngine(RestHighLevelClient client) {
        this.client = client;
    }

    public boolean isAvailable() {
        boolean ret = false;

        try {
            Response response = client.getLowLevelClient().performRequest(GET_METHOD, CLUSTER_HEALTH_ENDPOINT);
            String body = EntityUtils.toString(response.getEntity());
            Map jsonMap = new ObjectMapper().readValue(body, Map.class);
            if (jsonMap.containsKey("status")) {
                String status = jsonMap.get("status").toString();
                if ("yellow".equals(status) || "green".equals(status)) {
                    ret = true;
                } else {
                    LOGGER.warn("Cluster status not healthy: {}", status);
                }
            } else {
                LOGGER.warn("No status in _cluster/health response - {}", body);
            }
        } catch (ResponseException e) {
            LOGGER.warn("Caught ResponseException calling {}: {}", CLUSTER_HEALTH_ENDPOINT, e.getResponse().getStatusLine());
        } catch (IOException e) {
            LOGGER.error("Caught IOException calling _cluster/health: {}", e.getMessage());
        }

        return ret;
    }

    public void close() throws IOException {
        client.close();
    }

}
