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
import java.util.concurrent.atomic.AtomicInteger;

/**
 * A synchronous implementation of {@link EvaluationManager} - all queries
 * are run on a single thread.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class SynchronousEvaluationManager extends BaseEvaluationManager implements EvaluationManager {

    private final static Logger LOGGER = LogManager.getLogger(SynchronousEvaluationManager.class);

    private int queryCount;

    /**
     * Construct a synchronous (single-threaded) {@link EvaluationManager} instance to run
     * evaluations.
     *
     * @param platform           the search engine in use.
     * @param templateManager    the template manager.
     * @param persistenceManager the persistence manager.
     * @param fields             the fields to return from each query.
     * @param versions           the query versions to run.
     * @param versionTimestamp   the version timestamp.
     */
    public SynchronousEvaluationManager(SearchPlatform platform, QueryTemplateManager templateManager, PersistenceManager persistenceManager, String[] fields, Collection<String> versions, String versionTimestamp) {
        super(platform, templateManager, persistenceManager, fields, versions, versionTimestamp);
    }

    @Override
    public void evaluateQuery(Query query, String indexName, JsonNode queryNode, String defaultTemplate, int relevantDocCount) {
        LOGGER.info("\t\tQUERY: " + query.getName());
        queryCount++;

        getVersions().forEach(version -> {
            final AtomicInteger rank = new AtomicInteger(1);
            final QueryOrSearchResponse response = executeQuery(indexName, version, queryNode, defaultTemplate, relevantDocCount);

            query.setTotalHits(response.totalHits(), persistVersion(version));
            response.hits().forEach(hit -> query.collect(hit, rank.getAndIncrement(), persistVersion(version)));
        });

        completeQuery(query);
    }

    @Override
    public boolean isRunning() {
        return false;
    }

    @Override
    public int getQueriesRemaining() {
        return 0;
    }

    @Override
    public int getTotalQueries() {
        return queryCount;
    }
}
