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
package io.sease.rre.core.evaluation.impl;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.core.domain.Query;
import io.sease.rre.core.evaluation.EvaluationManager;
import io.sease.rre.core.template.QueryTemplateManager;
import io.sease.rre.persistence.PersistenceManager;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.Collection;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Simple asynchronous implementation of {@link EvaluationManager}. This
 * asynchronously runs evaluations using a threadpool, while the individual
 * versioned queries are run synchronously.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class AsynchronousEvaluationManager extends BaseEvaluationManager implements EvaluationManager {

    private final static Logger LOGGER = LogManager.getLogger(AsynchronousEvaluationManager.class);

    private final ThreadPoolExecutor executor;

    /**
     * Construct an asynchronous {@link EvaluationManager} instance to run
     * evaluations using a threadpool of a given size.
     *
     * @param platform           the search engine in use.
     * @param templateManager    the template manager.
     * @param persistenceManager the persistence manager.
     * @param fields             the fields to return from each query.
     * @param versions           the query versions to run.
     * @param versionTimestamp   the version timestamp.
     * @param threadpoolSize     the maximum number of threads to use.
     */
    public AsynchronousEvaluationManager(SearchPlatform platform,
                                         QueryTemplateManager templateManager,
                                         PersistenceManager persistenceManager,
                                         String[] fields,
                                         Collection<String> versions,
                                         String versionTimestamp,
                                         int threadpoolSize) {
        super(platform, templateManager, persistenceManager, fields, versions, versionTimestamp);
        this.executor = (ThreadPoolExecutor) Executors.newFixedThreadPool(threadpoolSize);
    }

    @Override
    public void evaluateQuery(Query query, String indexName, JsonNode queryNode, String defaultTemplate, int relevantDocCount) {
        evaluateQueryAsync(query, indexName, queryNode, defaultTemplate, relevantDocCount)
                .thenAccept(q -> {
                    LOGGER.info("\t\tQUERY: " + query.getName());
                    completeQuery(q);
                });
    }

    /**
     * Start an asynchronous evaluation where each query version is run
     * synchronously.
     *
     * @param query            the query to be evaluated.
     * @param indexName        the base name of the index to query.
     * @param queryNode        the JSON node holding details of the query template.
     * @param defaultTemplate  the fallback query template.
     * @param relevantDocCount the number of relevant documents required.
     * @return a Future which, when complete, will contain the evaluated query.
     */
    private CompletableFuture<Query> evaluateQueryAsync(Query query, String indexName, JsonNode queryNode, String defaultTemplate, int relevantDocCount) {
        return CompletableFuture.supplyAsync(() -> {
            final CountDownLatch doneSignal = new CountDownLatch(getVersions().size());
            getVersions().forEach(version -> {
                final AtomicInteger rank = new AtomicInteger(1);

                final QueryOrSearchResponse response = executeQuery(indexName, version, queryNode, defaultTemplate, relevantDocCount);
                query.setTotalHits(response.totalHits(), persistVersion(version));
                response.hits().forEach(hit -> query.collect(hit, rank.getAndIncrement(), persistVersion(version)));
                doneSignal.countDown();
            });
            try {
                doneSignal.await();
            } catch (InterruptedException e) {
                LOGGER.error("Interrupted waiting for queries to execute: {}", e.getMessage());
            }
            return query;
        }, executor);
    }

    @Override
    public boolean isRunning() {
        return executor.getCompletedTaskCount() < executor.getTaskCount();
    }

    @Override
    public int getQueriesRemaining() {
        return (int) (executor.getTaskCount() - executor.getCompletedTaskCount());
    }

    @Override
    public int getTotalQueries() {
        return (int) executor.getTaskCount();
    }
}
