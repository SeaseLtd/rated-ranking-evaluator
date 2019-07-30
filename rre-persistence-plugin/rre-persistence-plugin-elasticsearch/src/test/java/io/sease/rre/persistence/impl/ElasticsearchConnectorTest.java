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

import com.google.common.net.MediaType;
import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;
import org.junit.Before;
import org.junit.Ignore;
import org.junit.Rule;
import org.junit.Test;
import org.mockserver.client.MockServerClient;
import org.mockserver.junit.MockServerRule;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockserver.model.HttpRequest.request;
import static org.mockserver.model.HttpResponse.response;

/**
 * Unit tests for the Elasticsearch engine.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
@SuppressWarnings("UnstableApiUsage")
@Ignore
public class ElasticsearchConnectorTest {

    private ElasticsearchConnector searchEngine;

    @Rule
    public MockServerRule mockServerRule = new MockServerRule(this);

    private MockServerClient mockServerClient;

    @Before
    public void setupSearchEngine() {
        RestHighLevelClient client = new RestHighLevelClient(
                RestClient.builder(
                        HttpHost.create("http://localhost:" + mockServerRule.getPort())));
        searchEngine = new ElasticsearchConnector(client);
    }

    @Test
    public void isAvailableReturnsFalse_whenStatusIsBad() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(500).withReasonPhrase("Server error"));
        assertThat(searchEngine.isAvailable()).isFalse();
    }

    @Test
    public void isAvailableReturnsFalse_whenNoStatusInBody() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(200).withBody("{}", MediaType.JSON_UTF_8));
        assertThat(searchEngine.isAvailable()).isFalse();
    }

    @Test
    public void isAvailableReturnsFalse_whenStatusRed() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(200).withBody("{ \"status\": \"red\" }", MediaType.JSON_UTF_8));
        assertThat(searchEngine.isAvailable()).isFalse();
    }

    @Test
    public void isAvailableReturnsTrue_whenStatusYellow() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(200).withBody("{ \"status\": \"yellow\" }", MediaType.JSON_UTF_8));
        assertThat(searchEngine.isAvailable()).isTrue();
    }

    @Test
    public void isAvailableReturnsTrue_whenStatusGreen() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(200).withBody("{ \"status\": \"green\" }", MediaType.JSON_UTF_8));
        assertThat(searchEngine.isAvailable()).isTrue();
    }
}
