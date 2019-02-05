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
import io.sease.rre.persistence.PersistenceHandler;
import org.junit.After;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;
import java.io.FileWriter;
import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * Unit tests for the JSON PersistenceHandler implementation.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class JsonPersistenceHandlerTest {

    private static final String HANDLER_NAME = "jsonTest";

    @Rule
    public TemporaryFolder folder = new TemporaryFolder();

    private PersistenceHandler handler;

    @Before
    public void setupHandler() {
        this.handler = new JsonPersistenceHandler();
    }

    @After
    public void tearDownHandler() {
        this.handler = null;
    }

    @Test
    public void beforeStartThrowsException_whenFileCannotBeDeleted() throws Exception {
        File outDir = folder.newFolder();
        File outFile = new File(outDir, "temp.json");

        Map<String, Object> config = new HashMap<>();
        // Pass the output directory - won't be able to delete since not empty
        config.put(JsonPersistenceHandler.DESTINATION_FILE_CONFIGKEY, outDir.getAbsolutePath());
        handler.configure(HANDLER_NAME, config);

        try (FileWriter fw = new FileWriter(outFile)) {
            fw.write("blah");
            try {
                handler.beforeStart();
                fail("Expected PersistenceException");
            } catch (PersistenceException e) {
                // Expected behaviour
            }
        }
    }

    @Test
    public void beforeStartPasses_whenFileExists() throws Exception {
        File outFile = folder.newFile();

        Map<String, Object> config = new HashMap<>();
        config.put(JsonPersistenceHandler.DESTINATION_FILE_CONFIGKEY, outFile.getAbsolutePath());
        handler.configure(HANDLER_NAME, config);

        handler.beforeStart();
    }

    @Test
    public void beforeStartPasses_whenDestinationDirNotExist() throws Exception {
        Map<String, Object> config = new HashMap<>();
        config.put(JsonPersistenceHandler.DESTINATION_FILE_CONFIGKEY, folder.getRoot().getAbsolutePath() + "/target/rre/evaluation.json");
        handler.configure(HANDLER_NAME, config);

        handler.beforeStart();

        File target = new File(folder.getRoot(), "target/rre/evaluation.json");
        assertTrue(target.exists());
        assertTrue(target.canWrite());
    }

    @Test
    public void beforeStop_handlesEmptyQueryList() throws Exception {
        File outFile = folder.newFile();
        Map<String, Object> config = new HashMap<>();
        config.put(JsonPersistenceHandler.DESTINATION_FILE_CONFIGKEY, outFile.getAbsolutePath());
        config.put(JsonPersistenceHandler.PRETTY_CONFIGKEY, true);
        handler.configure(HANDLER_NAME, config);

        handler.beforeStop();

        assertTrue(outFile.exists());
        assertTrue(outFile.length() != 0);
    }
}
