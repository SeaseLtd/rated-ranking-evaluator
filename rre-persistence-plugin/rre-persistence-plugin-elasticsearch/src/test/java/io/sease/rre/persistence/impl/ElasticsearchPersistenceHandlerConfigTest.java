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

import io.sease.rre.persistence.PersistenceException;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.*;

/**
 * Unit tests for the ES persistence handler configuration handling.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class ElasticsearchPersistenceHandlerConfigTest {

    private ElasticsearchPersistenceHandler handler;

    @Before
    public void setupHandler() {
        this.handler = new ElasticsearchPersistenceHandler();
    }

    @After
    public void tearDownHandler() {
        this.handler = null;
    }

    @Test
    public void configureUsesDefaultHost_whenNoHttpHostsConfigured() {
        Map<String, Object> config = new HashMap<>();
        config.put(ElasticsearchPersistenceHandler.INDEX_KEY, "index");
        handler.configure("name", config);

        assertThat(handler.getBaseUrls()).isNotNull();
        assertThat(handler.getBaseUrls().get(0)).isEqualTo(ElasticsearchPersistenceHandler.DEFAULT_HOST);
    }

    @Test
    public void configureExtractsHosts_whenListGiven() {
        Map<String, Object> config = new HashMap<>();
        config.put(ElasticsearchPersistenceHandler.BASE_URL_KEY, Arrays.asList("http://elastic1:9200", "http://elastic2:9200"));
        config.put(ElasticsearchPersistenceHandler.INDEX_KEY, "index");
        handler.configure("name", config);

        assertThat(handler.getBaseUrls()).isNotNull();
        assertThat(handler.getBaseUrls().size()).isEqualTo(2);
        assertThat(handler.getBaseUrls()).contains("http://elastic1:9200", "http://elastic2:9200");
    }

    @Test
    public void configureExtractsHosts_whenStringGiven() {
        Map<String, Object> config = new HashMap<>();
        config.put(ElasticsearchPersistenceHandler.BASE_URL_KEY, "http://elastic1:9200");
        config.put(ElasticsearchPersistenceHandler.INDEX_KEY, "index");
        handler.configure("name", config);

        assertThat(handler.getBaseUrls()).isNotNull();
        assertThat(handler.getBaseUrls().size()).isEqualTo(1);
        assertThat(handler.getBaseUrls()).contains("http://elastic1:9200");
    }

    @Test(expected = IllegalArgumentException.class)
    public void configureThrowsIllegalArgException_whenIndexMissingFromConfig() {
        Map<String, Object> config = new HashMap<>();
        handler.configure("name", config);
    }

    @Test(expected = PersistenceException.class)
    public void beforeStartThrowsException_whenHostsNotAString() throws Exception {
        Map<String, Object> config = new HashMap<>();
        config.put(ElasticsearchPersistenceHandler.BASE_URL_KEY, 1);
        config.put(ElasticsearchPersistenceHandler.INDEX_KEY, "index");
        handler.configure("name", config);

        assertThat(handler.getBaseUrls()).isNotNull();

        handler.beforeStart();
    }

    @Test(expected = PersistenceException.class)
    public void beforeStartThrowsException_whenEmptyHostsList() throws Exception {
        Map<String, Object> config = new HashMap<>();
        config.put(ElasticsearchPersistenceHandler.BASE_URL_KEY, Collections.emptyList());
        config.put(ElasticsearchPersistenceHandler.INDEX_KEY, "index");
        handler.configure("name", config);

        assertThat(handler.getBaseUrls()).isNotNull();

        handler.beforeStart();
    }

    @Test(expected = PersistenceException.class)
    public void beforeStartThrowsException_withBadHostsList() throws Exception {
        Map<String, Object> config = new HashMap<>();
        config.put(ElasticsearchPersistenceHandler.BASE_URL_KEY, "this is not a URL");
        config.put(ElasticsearchPersistenceHandler.INDEX_KEY, "index");
        handler.configure("name", config);

        assertThat(handler.getBaseUrls()).isNotNull();

        handler.beforeStart();
    }
}
