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
package io.sease.rre.core.version;

import java.io.File;
import java.util.Collection;

/**
 * A manager for fetching the versions and version folders to be used during
 * an evaluation.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public interface VersionManager {

    /**
     * Retrieve the folders holding the configuration sets to be evaluated.
     * @return a collection of folders.
     */
    Collection<File> getConfigurationVersionFolders();

    /**
     * Retrieve the names of the configuration set versions to be evaluated.
     * @return a collection of strings holding the version names.
     */
    Collection<String> getConfigurationVersions();

    /**
     * Add explicitly a new config version
     * @param configVersion
     */
    void addConfigurationVersion(String configVersion);

    /**
     * Retrieve the version timestamp to use, if appropriate.
     *
     * This is set in the persistence configuration, and will only be set if
     * there is a single configuration set in use during this evaluation.
     *
     * @return the version timestamp, or {@code null} if not appropriate.
     */
    String getVersionTimestamp();
}
