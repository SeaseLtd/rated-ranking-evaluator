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

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * An implementation of the {@link QueryTemplateManager} that will cache the
 * template contents.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class CachingQueryTemplateManager implements QueryTemplateManager {

    private final Map<File, String> templatePathMap = new HashMap<>();
    private final File templatesFolder;

    /**
     * Initialise the query template manager with template folder path.
     *
     * @param templatesFolderPath the path to the template folder.
     * @throws IllegalArgumentException if the folder path doesn't point to a
     *                                  directory, or the directory cannot be read.
     */
    public CachingQueryTemplateManager(String templatesFolderPath) throws IllegalArgumentException {
        this.templatesFolder = new File(templatesFolderPath);
        if (!templatesFolder.isDirectory() || !templatesFolder.canRead()) {
            throw new IllegalArgumentException("Unable to read from query template directory " + templatesFolder.getAbsolutePath());
        }
    }

    @Override
    public String getTemplate(final String defaultTemplate, final String template, final String version) throws IOException {
        String templateName = Optional.ofNullable(getTemplate(defaultTemplate, template))
                .orElseThrow(() -> new IllegalArgumentException("No template name supplied!"));
        File templatePath = buildTemplatePath(templateName, version);
        templatePathMap.putIfAbsent(templatePath, readTemplateContent(templatePath));

        return templatePathMap.get(templatePath);
    }

    private String getTemplate(String defaultTemplate, String template) {
        return template == null ? defaultTemplate : template;
    }

    private File buildTemplatePath(String template, String version) {
        final File templateFile;

        if (template.contains(VERSION_PLACEHOLDER)) {
            templateFile = new File(getVersionedTemplateFolder(version), template.replace(VERSION_PLACEHOLDER, version));
        } else {
            templateFile = new File(getVersionedTemplateFolder(version), template);
        }

        return templateFile;
    }

    private File getVersionedTemplateFolder(String version) {
        File versionedFolder = new File(templatesFolder, version);
        return (versionedFolder.canRead() && versionedFolder.isDirectory()) ? versionedFolder : templatesFolder;
    }

    /**
     * Reads a template content.
     *
     * @param file the template file.
     * @return the template content.
     * @throws IOException      if the file cannot be read.
     * @throws RuntimeException if other exceptions are thrown (OutOfMemory, SecurityException).
     */
    private String readTemplateContent(final File file) throws IOException {
        try {
            return new String(Files.readAllBytes(file.toPath()));
        } catch (final IOException e) {
            throw e;
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }
}
