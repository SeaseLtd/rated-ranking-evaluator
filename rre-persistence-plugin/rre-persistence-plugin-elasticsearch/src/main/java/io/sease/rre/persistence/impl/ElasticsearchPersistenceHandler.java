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

import io.sease.rre.core.domain.Query;
import io.sease.rre.persistence.PersistenceException;
import io.sease.rre.persistence.PersistenceHandler;
import io.sease.rre.persistence.impl.connector.ElasticsearchConnector;
import io.sease.rre.persistence.impl.connector.ElasticsearchConnectorFactory;
import org.apache.http.HttpHost;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.*;
import java.util.concurrent.*;
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
    static final String INDEX_KEY = "index";
    static final String THREADPOOL_KEY = "threadpoolSize";
    static final String RUN_INTERVAL_KEY = "runIntervalMs";
    static final String BATCH_SIZE_KEY = "batchSize";

    static final String DEFAULT_HOST = "http://localhost:9200";
    static final int DEFAULT_THREADPOOL = 2;
    static final long DEFAULT_RUN_INTERVAL = 500;
    static final int DEFAULT_BATCHSIZE = 500;

    private final TransferQueue<Query> queryQueue = new LinkedTransferQueue<>();

    private String name;

    // Elasticsearch configuration
    private List<String> baseUrls;
    private String index;
    // Scheduler configuration
    private int threadpoolSize;
    private long runIntervalMs;
    private int batchSize;

    private ElasticsearchConnector elasticsearch;
    private ScheduledExecutorService scheduledExecutor;

    @Override
    @SuppressWarnings("unchecked")
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
        // Extract the index name - required
        if (!configuration.containsKey(INDEX_KEY)) {
            throw new IllegalArgumentException("Missing index from Elasticsearch persistence configuration!");
        }
        this.index = (String) configuration.get("index");

        // Extract the other properties, if set
        threadpoolSize = (int) configuration.getOrDefault(THREADPOOL_KEY, DEFAULT_THREADPOOL);
        runIntervalMs = (long) configuration.getOrDefault(RUN_INTERVAL_KEY, DEFAULT_RUN_INTERVAL);
        batchSize = (int) configuration.getOrDefault(BATCH_SIZE_KEY, DEFAULT_BATCHSIZE);
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public void beforeStart() throws PersistenceException {
        initialiseElasticsearchConnector();
        scheduledExecutor = new ScheduledThreadPoolExecutor(threadpoolSize);
    }

    private void initialiseElasticsearchConnector() throws PersistenceException {
        try {
            // Check the HTTP core library version is correct
            checkHttpHostVersion();

            // Convert hosts to HTTP host objects
            final HttpHost[] httpHosts = baseUrls.stream()
                    .map(HttpHost::create)
                    .toArray(HttpHost[]::new);

            // Initialise the client
            elasticsearch = new ElasticsearchConnectorFactory(new RestHighLevelClient(RestClient.builder(httpHosts))).buildConnector();
        } catch (final IOException e) {
            LOGGER.warn("Could not initialise ElasticsearchConnector :: {}", e.getMessage());
        } catch (final IllegalArgumentException e) {
            throw new PersistenceException(e);
        }
    }

    private void checkHttpHostVersion() throws PersistenceException {
        try {
            HttpHost.class.getDeclaredMethod("create", String.class);
        } catch (NoSuchMethodException e) {
            StringWriter sw = new StringWriter();
            PrintWriter pw = new PrintWriter(sw);
            pw.println("No HttpHost::create method available - add the following plugin dependencies:");
            pw.println("  org.apache.httpcomponents:httpcore:4.4+");
            pw.println("  org.apache.httpcomponents:httpclient:4.5+");
            pw.flush();
            throw new PersistenceException(sw.toString());
        }
    }

    @Override
    public void start() throws PersistenceException {
        // Make sure the cluster is alive
        if (!elasticsearch.isAvailable()) {
            throw new PersistenceException("Elasticsearch cluster at [" + String.join(", ", baseUrls) + "] not available!");
        }

        // Make sure the index exists or can be created
        ensureIndexExists();

        // Start the scheduled executor to store the queries in batches
        scheduledExecutor.scheduleAtFixedRate(new QueryStorageRunnable(), runIntervalMs, runIntervalMs, TimeUnit.MILLISECONDS);
    }

    private void ensureIndexExists() throws PersistenceException {
        try {
            if (!elasticsearch.indexExists(index)) {
                LOGGER.info("Creating index {}", index);
                if (!elasticsearch.createIndex(index)) {
                    LOGGER.warn("Could not create index {}", index);
                    throw new PersistenceException("Index " + index + " is not available for writing");
                }
            }
        } catch (IOException e) {
            throw new PersistenceException(e);
        }
    }

    @Override
    public void recordQuery(Query q) {
        if (!queryQueue.offer(q)) {
            LOGGER.warn("Query item rejected by queue");
        }
    }

    @Override
    public void beforeStop() {
        // Clear the query queue, if not empty
        while (!queryQueue.isEmpty()) {
            scheduledExecutor.execute(new QueryStorageRunnable());
        }
    }

    @Override
    public void stop() {
        // Wait for any final storage tasks to complete
        try {
            scheduledExecutor.awaitTermination(30, TimeUnit.SECONDS);
        } catch (final InterruptedException e) {
            LOGGER.error("Interrupted waiting for scheduled tasks to complete", e.getMessage());
        }

        // Close the ES connector
        try {
            elasticsearch.close();
        } catch (final IOException e) {
            LOGGER.error("Caught IOException closing Elasticsearch client :: " + e.getMessage());
        }
    }

    private class QueryStorageRunnable implements Runnable {

        @Override
        public void run() {
            Collection<Query> queuedQueries = new ArrayList<>(batchSize);
            queryQueue.drainTo(queuedQueries, batchSize);
            if (!queuedQueries.isEmpty()) {
                List<QueryVersionReport> reports = queuedQueries.stream()
                        .map(QueryVersionReport::fromQuery)
                        .flatMap(List::stream)
                        .collect(Collectors.toList());
                elasticsearch.storeItems(index, reports);
            }
        }
    }


    // Testing method
    List<String> getBaseUrls() {
        return baseUrls;
    }

    // Testing method
    void setElasticsearch(ElasticsearchConnector es) {
        this.elasticsearch = es;
    }
}
