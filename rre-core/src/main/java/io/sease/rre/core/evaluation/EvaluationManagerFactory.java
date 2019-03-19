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

import io.sease.rre.core.evaluation.impl.AsynchronousEvaluationManager;
import io.sease.rre.core.evaluation.impl.AsynchronousQueryEvaluationManager;
import io.sease.rre.core.evaluation.impl.SynchronousEvaluationManager;
import io.sease.rre.core.template.QueryTemplateManager;
import io.sease.rre.persistence.PersistenceManager;
import io.sease.rre.search.api.SearchPlatform;

import java.util.Collection;

/**
 * Factory class to instantiate the {@link EvaluationManager} implementation to
 * use to evaluate the queries.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public abstract class EvaluationManagerFactory {

    /**
     * Instantiate an {@link EvaluationManager}, based on the configuration given.
     *
     * @param evaluationConfiguration the evaluation configuration.
     * @param searchPlatform          the search platform in use.
     * @param persistenceManager      the persistence manager.
     * @param templateManager         the template manager.
     * @param fields                  the fields to return from each query.
     * @param versions                the versions being evaluated.
     * @param versionTimestamp        the version timestamp, if required.
     * @return an appropriate {@link EvaluationManager} for the configuration.
     */
    public static EvaluationManager instantiateEvaluationManager(
            final EvaluationConfiguration evaluationConfiguration,
            final SearchPlatform searchPlatform,
            final PersistenceManager persistenceManager,
            final QueryTemplateManager templateManager,
            final String[] fields,
            final Collection<String> versions,
            final String versionTimestamp) {
        final EvaluationManager evaluationManager;

        if (evaluationConfiguration.isRunAsync()) {
            if (evaluationConfiguration.isRunQueriesAsync()) {
                evaluationManager = new AsynchronousQueryEvaluationManager(searchPlatform, templateManager, persistenceManager, fields, versions, versionTimestamp, evaluationConfiguration.getThreadpoolSize());
            } else {
                evaluationManager = new AsynchronousEvaluationManager(searchPlatform, templateManager, persistenceManager, fields, versions, versionTimestamp, evaluationConfiguration.getThreadpoolSize());
            }
        } else {
            evaluationManager = new SynchronousEvaluationManager(searchPlatform, templateManager, persistenceManager, fields, versions, versionTimestamp);
        }

        return evaluationManager;
    }
}
