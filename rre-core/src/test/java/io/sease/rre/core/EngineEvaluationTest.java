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
package io.sease.rre.core;

import io.sease.rre.core.domain.DomainMember;
import io.sease.rre.core.domain.Evaluation;
import io.sease.rre.core.domain.metrics.MetricClassConfigurationManager;
import io.sease.rre.core.domain.metrics.MetricClassManager;
import io.sease.rre.core.evaluation.EvaluationConfiguration;
import io.sease.rre.core.evaluation.EvaluationManager;
import io.sease.rre.core.evaluation.EvaluationManagerFactory;
import io.sease.rre.core.template.QueryTemplateManager;
import io.sease.rre.core.template.impl.CachingQueryTemplateManager;
import io.sease.rre.core.version.VersionManager;
import io.sease.rre.persistence.PersistenceManager;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Unit tests for the Engine's evaluate method, attempting to ensure that
 * the returned output contains everything we think it should.
 *
 * @author Matt Pearce (matt@elysiansoftware.co.uk)
 */
public class EngineEvaluationTest {

    private static final String ID_FIELD = "id";
    private static final int MAX_VERSIONS = 16;
    private static final Collection<String> SIMPLE_METRICS = Arrays.asList(
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne",
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtTwo",
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtThree",
            "io.sease.rre.core.domain.metrics.impl.PrecisionAtTen"
    );
    private static final int THREADPOOL_SIZE = 8;
    @SuppressWarnings("rawtypes")
    private static final Map<String, Map> PARAMETERIZED_METRICS = new HashMap<>();
    private static final String COLLECTION = "basses";
    private static final String[] FIELDS = new String[]{ ID_FIELD };
    private static final int MAX_ROWS = 10;

    private static final String BASE_FOLDER_PATH = "src/test/resources/engine_evaluation_tests";
    private static final String RATINGS_FOLDER_PATH = BASE_FOLDER_PATH + "/ratings";
    private static final String TEMPLATES_FOLDER_PATH = BASE_FOLDER_PATH + "/templates";

    private static final Random random = new Random();

    private final SearchPlatform searchPlatform = mock(SearchPlatform.class);
    private final File corporaFolder = null;
    private final File ratingsFolder = new File(RATINGS_FOLDER_PATH);
    private final String checksumFilepath = null;
    private final QueryTemplateManager templateManager = new CachingQueryTemplateManager(TEMPLATES_FOLDER_PATH);
    private final PersistenceManager persistenceManager = mock(PersistenceManager.class);

    private List<String> versions;
    private VersionManager versionManager;
    private MetricClassManager metricClassManager;

    @BeforeClass
    public static void initialiseParameterisedMetrics() {
        final Map<String, Object> errConfig = new HashMap<>();
        errConfig.put("class", "io.sease.rre.core.domain.metrics.impl.ExpectedReciprocalRank");
        errConfig.put("k", 10);
        PARAMETERIZED_METRICS.put("ERR@10", errConfig);
    }

    @Before
    public void initialiseVersions() {
        final int numVersions = random.nextInt(MAX_VERSIONS) + 1;
        versions = new ArrayList<>(numVersions);
        for (int i = 0; i < numVersions; i ++) {
            versions.add("v" + i);
        }
        versionManager = mock(VersionManager.class);
        when(versionManager.getConfigurationVersions()).thenReturn(versions);
    }

    @Before
    public void initialiseMetrics() {
        metricClassManager = MetricClassConfigurationManager.getInstance()
                .buildMetricClassManager(SIMPLE_METRICS, PARAMETERIZED_METRICS);
    }

    @Before
    public void initialiseSearchPlatform() {
        when(searchPlatform.executeQuery(eq(COLLECTION), anyString(), anyString(), eq(FIELDS), eq(MAX_ROWS)))
                .thenReturn(generateRandomResults());
    }

    private QueryOrSearchResponse generateRandomResults() {
        final int numResults = random.nextInt(MAX_ROWS) + 1;
        final List<Map<String, Object>> results = new ArrayList<>(numResults);
        for (int i = numResults; i > 0; i --) {
            Map<String, Object> item = new HashMap<>();
            item.put(ID_FIELD, "" + (char)('a' + random.nextInt(26)) + random.nextInt());
            results.add(item);
        }
        return new QueryOrSearchResponse(numResults, results);
    }


    @Test
    public void runSynchronousTests() throws Exception {
        final EvaluationConfiguration evaluationConfiguration = mock(EvaluationConfiguration.class);
        when(evaluationConfiguration.isRunAsync()).thenReturn(false);
        EvaluationManager evaluationManager = EvaluationManagerFactory.instantiateEvaluationManager(evaluationConfiguration,
                searchPlatform, persistenceManager, templateManager, FIELDS, versions, null);

        final Engine engine = new Engine(searchPlatform, corporaFolder, ratingsFolder, checksumFilepath,
                metricClassManager, persistenceManager, versionManager, evaluationManager);
        Evaluation evaluation = engine.evaluate(Collections.emptyMap());

        // Verify the evaluation contains all the expected metrics
        verifyEvaluationMetricVersions(evaluation);
    }

    @Test
    public void runAsynchronousTests() throws Exception {
        final EvaluationConfiguration evaluationConfiguration = mock(EvaluationConfiguration.class);
        when(evaluationConfiguration.isRunAsync()).thenReturn(true);
        when(evaluationConfiguration.isRunQueriesAsync()).thenReturn(false);
        when(evaluationConfiguration.getThreadpoolSize()).thenReturn(THREADPOOL_SIZE);
        EvaluationManager evaluationManager = EvaluationManagerFactory.instantiateEvaluationManager(evaluationConfiguration,
                searchPlatform, persistenceManager, templateManager, FIELDS, versions, null);

        final Engine engine = new Engine(searchPlatform, corporaFolder, ratingsFolder, checksumFilepath,
                metricClassManager, persistenceManager, versionManager, evaluationManager);
        Evaluation evaluation = engine.evaluate(Collections.emptyMap());

        // Verify the evaluation contains all the expected metrics
        verifyEvaluationMetricVersions(evaluation);
    }

    @Test
    public void runAsynchronousQueryTests() throws Exception {
        final EvaluationConfiguration evaluationConfiguration = mock(EvaluationConfiguration.class);
        when(evaluationConfiguration.isRunAsync()).thenReturn(true);
        when(evaluationConfiguration.isRunQueriesAsync()).thenReturn(true);
        when(evaluationConfiguration.getThreadpoolSize()).thenReturn(THREADPOOL_SIZE);
        EvaluationManager evaluationManager = EvaluationManagerFactory.instantiateEvaluationManager(evaluationConfiguration,
                searchPlatform, persistenceManager, templateManager, FIELDS, versions, null);

        final Engine engine = new Engine(searchPlatform, corporaFolder, ratingsFolder, checksumFilepath,
                metricClassManager, persistenceManager, versionManager, evaluationManager);
        Evaluation evaluation = engine.evaluate(Collections.emptyMap());

        // Verify the evaluation contains all the expected metrics
        verifyEvaluationMetricVersions(evaluation);
    }

    private void verifyEvaluationMetricVersions(Evaluation evaluation) {
        assertThat(evaluation.getMetrics().size()).isEqualTo(SIMPLE_METRICS.size() + PARAMETERIZED_METRICS.size());
        verifyMetrics(evaluation);
        evaluation.getChildren().forEach(corpus -> {
            verifyMetrics(corpus);
            corpus.getChildren().forEach(topic -> {
                verifyMetrics(topic);
                topic.getChildren().forEach(queryGroup -> {
                    verifyMetrics(queryGroup);
                    queryGroup.getChildren().forEach(this::verifyMetrics);
                });
            });
        });
    }

    private void verifyMetrics(DomainMember<?> dm) {
        dm.getMetrics().values().forEach(m -> {
            assertThat(m.getVersions().keySet())
                    .as("Check versions for metric %s [%s] in %s", m.getName(), m.getClass().getSimpleName(), dm.getClass().getSimpleName())
                    .containsAll(versions);
            assertThat(m.getVersions().keySet()).containsOnlyElementsOf(versions);
        });
    }
}
