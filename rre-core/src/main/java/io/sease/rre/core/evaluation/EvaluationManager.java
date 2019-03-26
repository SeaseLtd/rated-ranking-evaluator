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
package io.sease.rre.core.evaluation;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.core.domain.Query;

/**
 * Manager class to evaluate queries and persist the results. Evaluations
 * may be synchronous or asynchronous - use the {@link #isRunning()} method
 * to detect if query evaluation is still in progress, and the
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public interface EvaluationManager {

    /**
     * Evaluate a query, executing all versions of the query against the
     * appropriate data set, and persist the results.
     *
     * @param query            the query object to evaluate, including all required
     *                         metrics and version details.
     * @param indexName        the base index name to query.
     * @param queryNode        the JSON node holding the query details.
     * @param defaultTemplate  the default template to use if there is no
     *                         query- or version-specific template available.
     * @param relevantDocCount the number of relevant documents to evaluate and
     *                         generate metrics against.
     */
    void evaluateQuery(Query query, String indexName, JsonNode queryNode, String defaultTemplate, int relevantDocCount);

    /**
     * @return {@code true} if there are evaluations running.
     */
    boolean isRunning();

    /**
     * @return the number of queries left to be evaluated.
     */
    int getQueriesRemaining();

    /**
     * @return the total number of queries that have been set for evaluation.
     */
    int getTotalQueries();
}
