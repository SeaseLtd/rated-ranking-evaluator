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
package io.sease.rre.search.api.impl;

import org.apache.solr.client.solrj.embedded.JettyConfig;
import org.apache.solr.client.solrj.impl.CloudSolrClient;
import org.apache.solr.client.solrj.impl.HttpSolrClient;
import org.apache.solr.cloud.MiniSolrCloudCluster;
import org.apache.solr.cloud.SolrCloudTestCase;
import org.junit.After;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

import static junit.framework.TestCase.assertTrue;
import static org.junit.Assert.assertNotNull;

/**
 * Unit tests for the SolrClientManager class.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class SolrClientManagerTest {

    private final String TARGET_INDEX = "targetIndex";

    @Rule
    public TemporaryFolder tempFolder = new TemporaryFolder();

    private SolrClientManager clientManager;

    @Before
    public void setupClientManager() {
        clientManager = new SolrClientManager();
    }

    @After
    public void shutdownClientManager() {
        clientManager.close();
    }

    @Test
    public void buildsHttpSolrClientForSingleHost() {
        ExternalApacheSolr.SolrSettings settings = new ExternalApacheSolr.SolrSettings(
                Collections.singletonList("http://localhost:8983/solr"), null, null, null, null);

        clientManager.buildSolrClient(TARGET_INDEX, settings);

        assertNotNull(clientManager.getSolrClient(TARGET_INDEX));
        assertTrue(clientManager.getSolrClient(TARGET_INDEX) instanceof HttpSolrClient);
    }
    

    @Test
    public void buildsCloudSolrClientForZkHosts() {
        ExternalApacheSolr.SolrSettings settings = new ExternalApacheSolr.SolrSettings(
                null, Arrays.asList("localhost:2181", "localhost:2182"), null, null, null);

        clientManager.buildSolrClient(TARGET_INDEX, settings);

        assertNotNull(clientManager.getSolrClient(TARGET_INDEX));
        assertTrue(clientManager.getSolrClient(TARGET_INDEX) instanceof CloudSolrClient);
    }
}
