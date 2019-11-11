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

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.File;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Optional;
import java.util.stream.Collectors;

import static io.sease.rre.Func.ONLY_DIRECTORIES;
import static io.sease.rre.Func.safe;
import static java.util.Arrays.stream;

/**
 * Basic implementation of the VersionManager interface.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class VersionManagerImpl implements VersionManager {

    private static final Logger LOGGER = LogManager.getLogger(VersionManagerImpl.class);

    private final Collection<File> configurationVersionFolders;
    private final Collection<String> configurationVersions;
    private final String versionTimestamp;

    public VersionManagerImpl(File configurationSetFolder, Collection<String> include, Collection<String> exclude, boolean useTimestampAsVersion) {
        configurationVersionFolders = Arrays.asList(
                findConfigurationFolders(configurationSetFolder,
                        Optional.ofNullable(include).orElse(Collections.emptyList()),
                        Optional.ofNullable(exclude).orElse(Collections.emptyList())));

        this.configurationVersions = configurationVersionFolders.stream()
                .map(File::getName)
                .sorted()
                .collect(Collectors.toList());
        versionTimestamp = useTimestampAsVersion ? calculateVersionTimestamp() : null;
    }

    private File[] findConfigurationFolders(File configurationSetFolder, Collection<String> include, Collection<String> exclude) {
        File[] emptyArray = new File[0];
        if (configurationSetFolder.listFiles() == null) {
            return emptyArray;
        } else {
            return safe(configurationSetFolder.listFiles(
                    file -> ONLY_DIRECTORIES.accept(file)
                            && (include.isEmpty() || include.contains(file.getName()) || include.stream().anyMatch(rule -> file.getName().matches(rule)))
                            && (exclude.isEmpty() || (!exclude.contains(file.getName()) && exclude.stream().noneMatch(rule -> file.getName().matches(rule))))));
        }
    }

    private String calculateVersionTimestamp() {
        final String ret;
        if (configurationVersions.size() == 1) {
            ret = String.valueOf(System.currentTimeMillis());
            LOGGER.info("Using local system timestamp as version tag : " + versionTimestamp);
        } else {
            LOGGER.warn("Persistence.useTimestampAsVersion == true, but multiple configurations exist - ignoring");
            ret = null;
        }
        return ret;
    }

    @Override
    public Collection<File> getConfigurationVersionFolders() {
        return configurationVersionFolders;
    }

    @Override
    public Collection<String> getConfigurationVersions() {
        return configurationVersions;
    }

    @Override
    public void addConfigurationVersion(String configVersion) {
        this.configurationVersions.add(configVersion);
    }

    @Override
    public String getVersionTimestamp() {
        return versionTimestamp;
    }
}
