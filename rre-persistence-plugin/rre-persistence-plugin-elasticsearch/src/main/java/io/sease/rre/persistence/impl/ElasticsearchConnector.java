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
package io.sease.rre.persistence.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.http.util.EntityUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.action.admin.indices.create.CreateIndexRequest;
import org.elasticsearch.action.admin.indices.create.CreateIndexResponse;
import org.elasticsearch.action.admin.indices.get.GetIndexRequest;
import org.elasticsearch.action.bulk.BulkProcessor;
import org.elasticsearch.action.bulk.BulkRequest;
import org.elasticsearch.action.bulk.BulkResponse;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.common.xcontent.XContentType;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
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

    private static final String MAPPINGS_FILE = "/es_config.json";

    static final String GET_METHOD = "GET";
    static final String CLUSTER_HEALTH_ENDPOINT = "/_cluster/health";
    static final String DOC_MAPPING_TYPE = "_doc";

    private final RestHighLevelClient client;
    private final ObjectMapper mapper = new ObjectMapper();

    public ElasticsearchConnector(RestHighLevelClient client) {
        this.client = client;
    }

    /**
     * Is the Elasticsearch cluster available (and healthy)?
     * <p>
     * If this is not true, we won't be able to write anything to
     * Elasticsearch, so the persistence handler should fail.
     *
     * @return {@code true} if the Elasticsearch cluster is available and
     * healthy (ie. the cluster health status is green or yellow).
     */
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

    /**
     * Check whether or not an index exists.
     *
     * @param index the name of the index to check.
     * @return {@code true} if the index exists.
     * @throws IOException if a problem occurs calling the server.
     */
    public boolean indexExists(String index) throws IOException {
        return client.indices().exists(new GetIndexRequest().indices(index));
    }

    /**
     * Create an index, using the mappings read from the mappings file.
     *
     * @param index the name of the index to create.
     * @return {@code true} if the index was successfully created.
     * @throws IOException if there are problems reading the mappings, or
     *                     making the index creation request.
     */
    public boolean createIndex(String index) throws IOException {
        // Build the request
        CreateIndexRequest request = new CreateIndexRequest(index)
                .source(readConfig(), XContentType.JSON);

        CreateIndexResponse response = client.indices().create(request);

        return response.isAcknowledged();
    }

    private String readConfig() throws IOException {
        StringBuilder builder = new StringBuilder();

        try (BufferedReader br = new BufferedReader(new InputStreamReader(this.getClass().getResourceAsStream(MAPPINGS_FILE)))) {
            String line;
            while ((line = br.readLine()) != null) {
                builder.append(line);
            }
        } catch (IOException e) {
            LOGGER.error("IOException reading mappings :: {}", e.getMessage());
            throw (e);
        }

        return builder.toString();
    }

    /**
     * Store a collection of items to an Elasticsearch index.
     *
     * @param index   the index the items should be written to.
     * @param reports the items to store.
     */
    public void storeItems(String index, Collection<QueryVersionReport> reports) {
        BulkProcessor.Listener listener = new BulkProcessor.Listener() {
            @Override
            public void beforeBulk(long l, BulkRequest bulkRequest) {
                LOGGER.debug("About to execute bulk request of {} actions", bulkRequest.numberOfActions());
            }

            @Override
            public void afterBulk(long l, BulkRequest bulkRequest, BulkResponse bulkResponse) {
                if (bulkResponse.hasFailures()) {
                    LOGGER.warn("Bulk update request had failures!");
                    LOGGER.warn(bulkResponse.buildFailureMessage());
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

    /**
     * Close the Elasticsearch connector.
     *
     * @throws IOException if problems occur closing the connection.
     */
    public void close() throws IOException {
        client.close();
    }
}
