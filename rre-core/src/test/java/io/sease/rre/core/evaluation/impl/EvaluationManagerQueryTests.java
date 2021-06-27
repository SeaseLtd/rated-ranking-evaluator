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
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.Query;
import io.sease.rre.core.evaluation.EvaluationManager;
import io.sease.rre.core.template.QueryTemplateManager;
import io.sease.rre.persistence.PersistenceManager;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import static org.mockito.Mockito.any;
import static org.mockito.Mockito.anyInt;
import static org.mockito.Mockito.eq;
import static org.mockito.Mockito.isA;
import static org.mockito.Mockito.isNull;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Unit tests for synchronous evaluation manager queries.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class EvaluationManagerQueryTests {

    private static final String ID_FIELD = "id";
    private static final String TEMPLATE = "query.json";
    private static final Collection<String> DOC_IDS = Arrays.asList("1234", "3456");
    private static final String QUERY_TEXT = "fred";
    private static final String INDEX_NAME = "index";
    private static final String QUERY_TEMPLATE = "q=$query";
    private static final String WRONG_QUERY_TEMPLATE = "invalidQuery";
    private static final String QUERY_VALUE = "q=" + QUERY_TEXT;
    private static final int THREADPOOL_SIZE = 4;

    private final SearchPlatform platform = mock(SearchPlatform.class);
    private final PersistenceManager persistenceManager = mock(PersistenceManager.class);
    private final QueryTemplateManager templateManager = mock(QueryTemplateManager.class);
    private final String[] fields = new String[0];
    private final Collection<String> versions = Arrays.asList("v1.0", "v1.1");

    private Query query;
    private JsonNode queryNode;
    private JsonNode queryNodeWithWrongTemplate;


    private static final String WRONG_TEMPLATE = "wrong_query.json";

    @Before
    public void setup() throws Exception {
        query = buildQuery();
        queryNode = buildQueryNode(TEMPLATE);
        queryNodeWithWrongTemplate = buildQueryNode(WRONG_TEMPLATE);

        // Set up template manager
        when(templateManager.getTemplate(isNull(), eq(TEMPLATE), isA(String.class))).thenReturn(QUERY_TEMPLATE);
        when(templateManager.getTemplate(isNull(), eq(WRONG_TEMPLATE), isA(String.class))).thenReturn(WRONG_QUERY_TEMPLATE);

        // Set up platform for each version query
        versions.forEach(v -> when(platform.executeQuery(eq(INDEX_NAME), eq(v), eq(QUERY_VALUE), any(String[].class), anyInt()))
                .thenReturn(new QueryOrSearchResponse(0, Collections.emptyList())));

        versions.forEach(v -> when(platform.executeQuery(eq(INDEX_NAME), eq(v), eq(WRONG_QUERY_TEMPLATE), any(String[].class), anyInt()))
                .thenReturn(new QueryOrSearchResponse("Error")));
    }


    @Test
    public void evaluateQuery_synchronous() {
        final EvaluationManager evaluationManager = new SynchronousEvaluationManager(platform, templateManager, persistenceManager, fields, versions, null);

        evaluateAndWaitUntilDone(evaluationManager);

        verifyPersistence();
        verifySearchPlatform();
    }

    @Test
    public void evaluateQuery_asynchronous() {
        final EvaluationManager evaluationManager = new AsynchronousEvaluationManager(platform, templateManager, persistenceManager, fields, versions, null, THREADPOOL_SIZE);

        evaluateAndWaitUntilDone(evaluationManager);

        verifyPersistence();
        verifySearchPlatform();
    }


    @Test
    public void evaluateQueryWithErrors_synchronous(){

        EvaluationManager evaluationManager = new SynchronousEvaluationManager(platform, templateManager, persistenceManager, fields, versions, null);
        evaluateAndWaitQueriesWithErrorUntilDone(evaluationManager);

        Assert.assertEquals(2, evaluationManager.getTotalQueries());
        Assert.assertEquals(0, evaluationManager.getQueriesRemaining());
        Assert.assertEquals(4, evaluationManager.getTotalQueryExecutions());
        Assert.assertEquals(0, evaluationManager.getRemainingQueryExecutions());
        Assert.assertEquals(2, evaluationManager.getFailedQueries());
    }

    @Test
    public void evaluateQueryWithErrors_aynchronousVersions(){

        EvaluationManager evaluationManager = new AsynchronousEvaluationManager(platform, templateManager, persistenceManager, fields, versions, null, THREADPOOL_SIZE);
        evaluateAndWaitQueriesWithErrorUntilDone(evaluationManager);

        Assert.assertEquals(2, evaluationManager.getTotalQueries());
        Assert.assertEquals(0, evaluationManager.getQueriesRemaining());
        Assert.assertEquals(4, evaluationManager.getTotalQueryExecutions());
        Assert.assertEquals(0, evaluationManager.getRemainingQueryExecutions());
        Assert.assertEquals(2, evaluationManager.getFailedQueries());
    }


    @Test
    public void evaluateQueryWithErrors_asynchronousQueries(){

        EvaluationManager evaluationManager = new AsynchronousQueryEvaluationManager(platform, templateManager, persistenceManager, fields, versions, null, THREADPOOL_SIZE);
        evaluateAndWaitQueriesWithErrorUntilDone(evaluationManager);

        Assert.assertEquals(2, evaluationManager.getTotalQueries());
        Assert.assertEquals(0, evaluationManager.getQueriesRemaining());
        Assert.assertEquals(4, evaluationManager.getTotalQueryExecutions());
        Assert.assertEquals(0, evaluationManager.getRemainingQueryExecutions());
        Assert.assertEquals(2, evaluationManager.getFailedQueries());
    }



    private void evaluateAndWaitQueriesWithErrorUntilDone(EvaluationManager evaluationManager) {
        evaluationManager.evaluateQuery(query, INDEX_NAME, queryNodeWithWrongTemplate, null, DOC_IDS.size());
        evaluationManager.evaluateQuery(query, INDEX_NAME, queryNode, null, DOC_IDS.size());

        while (evaluationManager.isRunning()) {
            try { Thread.sleep(100); } catch (InterruptedException ignored) { }
        }
    }

    private void evaluateAndWaitUntilDone(EvaluationManager evaluationManager) {
        evaluationManager.evaluateQuery(query, INDEX_NAME, queryNode, null, DOC_IDS.size());

        while (evaluationManager.isRunning()) {
            try { Thread.sleep(100); } catch (InterruptedException ignored) { }
        }
    }

    private void verifyPersistence() {
        verify(persistenceManager).recordQuery(query);
    }

    private void verifySearchPlatform() {
        versions.forEach(v -> verify(platform).executeQuery(eq(INDEX_NAME), eq(v), eq(QUERY_VALUE), eq(fields), anyInt()));
    }

    private static Query buildQuery() throws IOException {
        final Query q = new Query();

        JsonNode relevantDocs = buildRelevantDocuments();

        q.setName(QUERY_TEXT);
        q.setIdFieldName(ID_FIELD);
        q.setRelevantDocuments(relevantDocs);
        q.prepare(Collections.emptyList());

        return q;
    }

    private static JsonNode buildRelevantDocuments() throws IOException {
        Map<String, Collection<String>> ratedDocs = new HashMap<>();
        ratedDocs.put("1", DOC_IDS);

        ObjectMapper mapper = new ObjectMapper();
        return mapper.readTree(mapper.writeValueAsString(ratedDocs));
    }

    private static JsonNode buildQueryNode(String template) throws IOException {
        final String qNode = "{ \"template\": \"" + template + "\", \"placeholders\": { \"$query\": \"" + QUERY_TEXT + "\" }}";
        return new ObjectMapper().readTree(qNode);
    }


}
