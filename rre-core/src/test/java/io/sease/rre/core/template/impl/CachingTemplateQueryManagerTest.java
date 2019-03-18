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
package io.sease.rre.core.template.impl;

import io.sease.rre.core.template.QueryTemplateManager;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

/**
 * Unit tests for the Caching QueryTemplateManager implementation.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class CachingTemplateQueryManagerTest {

    @Rule
    public TemporaryFolder folder = new TemporaryFolder();

    private QueryTemplateManager templateManager;

    @Before
    public void initialiseTemplateManager() {
        this.templateManager = new CachingQueryTemplateManager(folder.getRoot().getAbsolutePath());
    }

    @Test(expected=java.lang.IllegalArgumentException.class)
    public void constructor_throwsExceptionForNonExistentConfigDirectory() {
        final String path = folder.getRoot().getAbsolutePath() + "1";
        new CachingQueryTemplateManager(path);
    }


    @Test(expected=java.lang.IllegalArgumentException.class)
    public void getTemplate_throwsExceptionWhenNoTemplateSupplied() throws Exception {
        templateManager.getTemplate(null, null, "1.0");
    }

    @Test
    public void getTemplate_returnsDefaultWhenTemplateIsNull() throws Exception {
        final String defTemplate = "default.json";
        createTempFile(folder.getRoot(), defTemplate, defTemplate);

        String template = templateManager.getTemplate(defTemplate, null, "1.0");

        assertNotNull(template);
        assertEquals(defTemplate, template);
    }

    @Test
    public void getTemplate_returnsTemplate() throws Exception {
        final String defTemplate = "default.json";
        final String vTemplate = "query.json";
        createTempFile(folder.getRoot(), defTemplate, defTemplate);
        createTempFile(folder.getRoot(), vTemplate, vTemplate);

        String template = templateManager.getTemplate(defTemplate, vTemplate, "1.0");

        assertNotNull(template);
        assertEquals(vTemplate, template);
    }

    @Test
    public void getTemplate_returnsTemplateWhenDefaultIsNull() throws Exception {
        final String vTemplate = "query.json";
        createTempFile(folder.getRoot(), vTemplate, vTemplate);

        String template = templateManager.getTemplate(null, vTemplate, "1.0");

        assertNotNull(template);
        assertEquals(vTemplate, template);
    }

    @Test
    public void getTemplate_returnsVersionedTemplateFromFolder() throws Exception {
        final String version = "v1.0";
        final String baseTemplate = "query.json";
        createTempFile(folder.getRoot(), baseTemplate, baseTemplate);
        final String versionTemplate = "query_v1.json";
        final File versionFolder = folder.newFolder(version);
        createTempFile(versionFolder, versionTemplate, versionTemplate);

        String template = templateManager.getTemplate(null, versionTemplate, version);

        assertNotNull(template);
        assertEquals(versionTemplate, template);
    }

    @Test
    public void getTemplate_returnsVersionedTemplateWithPlaceholder() throws Exception {
        final String version = "v1.0";
        final String baseTemplate = "query.json";
        createTempFile(folder.getRoot(), baseTemplate, baseTemplate);
        final String versionTemplate = "query_v1.0.json";
        createTempFile(folder.getRoot(), versionTemplate, versionTemplate);

        String template = templateManager.getTemplate(null, "query_${version}.json", version);

        assertNotNull(template);
        assertEquals(versionTemplate, template);
    }

    @Test(expected=IOException.class)
    public void getTemplate_throwsExceptionWhenNoTemplateFile() throws Exception {
        final String vTemplate = "query.json";
        templateManager.getTemplate(null, vTemplate, "1.0");
    }


    private void createTempFile(File destFolder, String fileName, String content) {
        try {
            File outFile = new File(destFolder, fileName);
            Files.write(outFile.toPath(), content.getBytes());
        } catch (IOException e) {
            System.err.println("IO Exception writing temp file: " + e.getMessage());
        }
    }
}
