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

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Test;

import java.io.InputStream;
import java.util.Collections;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/**
 * Unit tests for the Solr settings.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class SolrSettingsTest {

    @Test
    public void canDeserializeSimpleSettings() throws Exception {
        InputStream is = SolrSettingsTest.class.getResourceAsStream("/solr-settings-simple.json");
        ObjectMapper mapper = new ObjectMapper();
        ExternalApacheSolr.SolrSettings settings = mapper.readValue(is, ExternalApacheSolr.SolrSettings.class);

        assertNotNull(settings);
        assertFalse(settings.getBaseUrls().isEmpty());
        assertFalse(settings.hasZookeeperSettings());
    }

    @Test
    public void canDeserializeEmptyZookeeperSettings() throws Exception {
        InputStream is = SolrSettingsTest.class.getResourceAsStream("/solr-settings-zk_empty.json");
        ObjectMapper mapper = new ObjectMapper();
        ExternalApacheSolr.SolrSettings settings = mapper.readValue(is, ExternalApacheSolr.SolrSettings.class);

        assertNotNull(settings);
        assertFalse(settings.getBaseUrls().isEmpty());
        assertFalse(settings.hasZookeeperSettings());
    }

    @Test
    public void canDeserializeZookeeperSettings() throws Exception {
        InputStream is = SolrSettingsTest.class.getResourceAsStream("/solr-settings-zk.json");
        ObjectMapper mapper = new ObjectMapper();
        ExternalApacheSolr.SolrSettings settings = mapper.readValue(is, ExternalApacheSolr.SolrSettings.class);

        assertNotNull(settings);
        assertFalse(settings.getBaseUrls().isEmpty());
        assertTrue(settings.hasZookeeperSettings());
        assertNotNull(settings.getConnectionTimeout());
        assertNotNull(settings.getSocketTimeout());
    }


    @Test(expected=java.lang.IllegalArgumentException.class)
    public void constructorThrowsException_whenNoURLsSet() {
        new ExternalApacheSolr.SolrSettings(null, null, null, null, null, null);
    }

    @Test
    public void canConstructWithZkHostsOnly() {
        ExternalApacheSolr.SolrSettings settings = new ExternalApacheSolr.SolrSettings(null, null, Collections.singletonList("localhost:2181"), null, null, null);
        assertNotNull(settings);
        assertTrue(settings.hasZookeeperSettings());
    }
}
