package io.sease.rre.persistence.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.http.util.EntityUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.action.bulk.BulkProcessor;
import org.elasticsearch.action.bulk.BulkRequest;
import org.elasticsearch.action.bulk.BulkResponse;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.common.xcontent.XContentType;

import java.io.IOException;
import java.util.Collection;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Elasticsearch search engine, for handling interactions with Elasticsearch
 * directly.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class ElasticsearchConnector {

    private static final Logger LOGGER = LogManager.getLogger(ElasticsearchConnector.class);

    static final String GET_METHOD = "GET";
    static final String CLUSTER_HEALTH_ENDPOINT = "/_cluster/health";
    static final String DOC_MAPPING_TYPE = "doc";

    private final RestHighLevelClient client;
    private final ObjectMapper mapper = new ObjectMapper();

    public ElasticsearchConnector(RestHighLevelClient client) {
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

    public void storeItems(String index, Collection<QueryVersionReport> reports) {
        BulkProcessor.Listener listener = new BulkProcessor.Listener() {
            @Override
            public void beforeBulk(long l, BulkRequest bulkRequest) {
                LOGGER.debug("About to execute bulk request of {} actions", bulkRequest.numberOfActions());
            }

            @Override
            public void afterBulk(long l, BulkRequest bulkRequest, BulkResponse bulkResponse) {
                if (bulkResponse.hasFailures()) {
                    LOGGER.error("Bulk update request had failures!");
                    LOGGER.error(bulkResponse.buildFailureMessage());
                }
            }

            @Override
            public void afterBulk(long l, BulkRequest bulkRequest, Throwable throwable) {
                LOGGER.error("Caught exception while executing bulk request: " + throwable.getMessage());
            }
        };

        BulkProcessor processor = BulkProcessor.builder(client::bulkAsync, listener).build();

        reports.forEach(r -> processor.add(
                new IndexRequest(index, DOC_MAPPING_TYPE, r.getId())
                        .source(convertReportToJson(r), XContentType.JSON)));

        processor.flush();
        try {
            if (!processor.awaitClose(30, TimeUnit.SECONDS)) {
                LOGGER.warn("Bulk update processor was terminated before it could complete operations!");
            }
        } catch (InterruptedException e) {
            LOGGER.error("Bulk update processor was interrupted before it could be closed :: {}", e.getMessage());
        }
    }

    private String convertReportToJson(QueryVersionReport report) {
        String json = null;

        try {
            json = mapper.writeValueAsString(report);
        } catch (JsonProcessingException e) {
            LOGGER.error("Could not convert versioned query report to JSON for Elasticsearch: ", e.getMessage());
        }

        return json;
    }

    public void close() throws IOException {
        client.close();
    }
}
