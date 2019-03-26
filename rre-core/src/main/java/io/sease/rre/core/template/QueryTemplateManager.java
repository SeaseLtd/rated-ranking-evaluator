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
package io.sease.rre.core.template;

import java.io.FileNotFoundException;
import java.io.IOException;

/**
 * Manager interface for the management of query templates.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public interface QueryTemplateManager {

    static final String VERSION_PLACEHOLDER = "${version}";

    /**
     * Retrieve the appropriate content for the required query template.
     * This allows for the template name to have a version placeholder
     * included, and for the template to be in a version-specific folder. If
     * no file exists, with or without versions, the content of the default
     * template will be returned.
     *
     * @param defaultTemplate the default (fallback) template.
     * @param template        the filename of the required template, with optional
     *                        version placeholder.
     * @param version         the version of the template required.
     * @return the content of the template.
     * @throws FileNotFoundException if no file can be found to match the
     *                               required template or default template values.
     * @throws IOException           if problems occur reading the content from the file.
     */
    String getTemplate(String defaultTemplate, String template, String version) throws FileNotFoundException, IOException;
}
