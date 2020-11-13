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

import io.sease.rre.search.api.SearchPlatform;
import org.junit.After;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class ElasticsearchTest {

    private static final String INDEX_NAME = "test";
    private static final String VERSION = "1.0";

    @Rule
    public TemporaryFolder tempFolder = new TemporaryFolder();

    private static SearchPlatform platform;

    @BeforeClass
    public static void configureEsNettySettings() {
        // This is a set-once property - when running the tests through Maven,
        // it gets set multiple times unless we disable that behaviour here
        System.setProperty("es.set.netty.runtime.available.processors", "false");
    }

    @Before
    public void setupPlatform() {
        platform = new Elasticsearch();
    }

    @After
    public void tearDownPlatform() {
        platform = null;
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenDirectory() throws Exception {
        File dummyFile = tempFolder.newFolder();
        assertFalse(platform.isSearchPlatformConfiguration(INDEX_NAME, dummyFile));
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenFileIsNotESConfig() throws Exception {
        File dummyFile = tempFolder.newFile();
        assertFalse(platform.isSearchPlatformConfiguration(INDEX_NAME, dummyFile));
    }

    @Test
    public void isSearchPlatformFile_returnsTrueWhenDirectoryContainsConfig() throws Exception {
        File configFile = tempFolder.newFile("index-shape.json");
        assertTrue(platform.isSearchPlatformConfiguration(INDEX_NAME, configFile));
    }


    @Test
    public void checkCollection_returnsFalseWhenNotLoaded() throws Exception {
        Map<String, Object> configuration = buildConfiguration();
        platform.beforeStart(configuration);
        platform.start();
        assertFalse(platform.checkCollection(INDEX_NAME, VERSION));
        platform.close();
    }

    @Test
    public void checkCollection_returnsTrueWhenInitialised() throws Exception {
        Map<String, Object> configuration = buildConfiguration();
        platform.beforeStart(configuration);
        platform.start();
        platform.load(
                new File(this.getClass().getResource("/elasticsearch/corpora/electric_basses.bulk").getPath()),
                new File(this.getClass().getResource("/elasticsearch/configuration_sets/v1.0/index-shape.json").getPath()),
                INDEX_NAME, VERSION);
        assertTrue(platform.checkCollection(INDEX_NAME, VERSION));
        platform.close();
    }

    private Map<String, Object> buildConfiguration() throws IOException {
        Map<String, Object> configuration = new HashMap<>();
        File homeFolder = tempFolder.newFolder();
        File dataFolder = tempFolder.newFolder();
        configuration.put("path.home", homeFolder.getAbsolutePath());
        configuration.put("path.data", dataFolder.getAbsolutePath());
        configuration.put("forceRefresh", Boolean.FALSE);
        return configuration;
    }
}
