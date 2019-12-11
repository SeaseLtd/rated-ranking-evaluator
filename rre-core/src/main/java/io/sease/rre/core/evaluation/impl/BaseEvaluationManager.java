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
import io.sease.rre.core.Engine;
import io.sease.rre.core.domain.Query;
import io.sease.rre.core.template.QueryTemplateManager;
import io.sease.rre.persistence.PersistenceManager;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;

import java.util.Collection;
import java.util.Iterator;
import java.util.Optional;

import static java.util.Optional.ofNullable;

/**
 * Base evaluation manager class, defining methods shared between
 * implementations.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
abstract class BaseEvaluationManager {

    private final SearchPlatform platform;
    private final QueryTemplateManager templateManager;
    private final PersistenceManager persistenceManager;
    private final String[] fields;
    private final Collection<String> versions;
    private final String versionTimestamp;

    BaseEvaluationManager(SearchPlatform platform,
                          QueryTemplateManager templateManager,
                          PersistenceManager persistenceManager,
                          String[] fields,
                          Collection<String> versions,
                          String versionTimestamp) {
        this.platform = platform;
        this.templateManager = templateManager;
        this.persistenceManager = persistenceManager;
        this.fields = fields;
        this.versions = versions;
        this.versionTimestamp = versionTimestamp;
    }


    Collection<String> getVersions() {
        return versions;
    }

    QueryOrSearchResponse executeQuery(String indexName, String version, JsonNode queryNode, String defaultTemplate, int relevantDocCount) {
        return platform.executeQuery(
                indexName, version,
                query(queryNode, defaultTemplate, version),
                fields,
                Math.max(10, relevantDocCount));
    }

    /**
     * Finalize the query evaluation, completing metric calculations
     * and persisting the completed query.
     *
     * @param query the query.
     */
    void completeQuery(Query query) {
        query.notifyCollectedMetrics();
        persistenceManager.recordQuery(query);
    }

    /**
     * Returns a query (as a string) that will be used for executing a specific evaluation.
     * A query string is the result of replacing all placeholders found in the template.
     *
     * @param queryNode       the JSON query node (in ratings configuration).
     * @param defaultTemplate the default template that will be used if a query doesn't declare it.
     * @param version         the version being executed.
     * @return a query (as a string) that will be used for executing a specific evaluation.
     */
    private String query(final JsonNode queryNode, final String defaultTemplate, final String version) {
        // try to see if the query declares a template
        String template = getQueryTemplate(queryNode).orElse(null);
        try {
            // EE case
            if (template == null && defaultTemplate == null) {
                return queryNode.toString();
            } else {
                String query = templateManager.getTemplate(defaultTemplate, template, version);
                for (final Iterator<String> iterator = queryNode.get("placeholders").fieldNames(); iterator.hasNext(); ) {
                    final String name = iterator.next();
                    query = query.replace(name, queryNode.get("placeholders").get(name).asText());
                }
                return query;
            }
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private Optional<String> getQueryTemplate(JsonNode queryNode) {
        return ofNullable(queryNode.get("template")).map(JsonNode::asText);
    }

    /**
     * Get the version to store when persisting query results.
     *
     * @param configVersion the configuration set version being evaluated.
     * @return the given configVersion, or the version timestamp if and only
     * if it is set (eg. there is a single version, and the persistence
     * configuration indicates a timestamp should be used to version this
     * evaluation data).
     */
    String persistVersion(final String configVersion) {
        return ofNullable(versionTimestamp).orElse(configVersion);
    }
}
