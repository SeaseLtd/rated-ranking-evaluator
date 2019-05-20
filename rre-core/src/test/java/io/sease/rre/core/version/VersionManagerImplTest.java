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

import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;
import java.nio.file.Files;
import java.util.Collections;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;

/**
 * Unit tests for the version manager implementation.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class VersionManagerImplTest {

    @Rule
    public TemporaryFolder tmp = new TemporaryFolder();

    private File configFolder;

    @Before
    public void setupConfigFolder() throws Exception {
        configFolder = tmp.newFolder();
    }

    @Test(expected=IllegalArgumentException.class)
    public void constructorThrowsIllegalArgument_whenNoFoldersAvailable() {
        new VersionManagerImpl(configFolder, null, null, false);
    }

    @Test
    public void constructorInitialisesWithSingleFolder() throws Exception {
        File v1 = new File(configFolder, "v1");
        Files.createDirectory(v1.toPath());

        VersionManager vm = new VersionManagerImpl(configFolder, null, null, false);

        assertThat(vm.getConfigurationVersionFolders()).containsExactly(v1);
        assertThat(vm.getConfigurationVersions()).containsExactly("v1");
        assertThat(vm.getVersionTimestamp()).isNull();
    }

    @Test
    public void constructorInitialisesWithMultipleFolders() throws Exception {
        File v1 = new File(configFolder, "v1");
        Files.createDirectory(v1.toPath());
        File v2 = new File(configFolder, "v2");
        Files.createDirectory(v2.toPath());
        File x1 = new File(configFolder, "x1");
        Files.createDirectory(x1.toPath());

        VersionManager vm = new VersionManagerImpl(configFolder, null, null, false);

        assertThat(vm.getConfigurationVersionFolders()).contains(v1, v2, x1);
        assertThat(vm.getConfigurationVersions()).containsExactly("v1", "v2", "x1");
        assertThat(vm.getVersionTimestamp()).isNull();
    }

    @Test
    public void constructorInitialisesWithIncludes() throws Exception {
        File v1 = new File(configFolder, "v1");
        Files.createDirectory(v1.toPath());
        File v2 = new File(configFolder, "v2");
        Files.createDirectory(v2.toPath());

        VersionManager vm = new VersionManagerImpl(configFolder, Collections.singleton("v2"), null, false);

        assertThat(vm.getConfigurationVersionFolders()).containsExactly(v2);
        assertThat(vm.getConfigurationVersions()).containsExactly("v2");
        assertThat(vm.getVersionTimestamp()).isNull();
    }

    @Test
    public void constructorInitialisesWithExcludes() throws Exception {
        File v1 = new File(configFolder, "v1");
        Files.createDirectory(v1.toPath());
        File v2 = new File(configFolder, "v2");
        Files.createDirectory(v2.toPath());

        VersionManager vm = new VersionManagerImpl(configFolder, null, Collections.singleton("v2"), false);

        assertThat(vm.getConfigurationVersionFolders()).containsExactly(v1);
        assertThat(vm.getConfigurationVersions()).containsExactly("v1");
        assertThat(vm.getVersionTimestamp()).isNull();
    }

    @Test
    public void constructorInitialisesWithVersionTimestamp() throws Exception {
        File v1 = new File(configFolder, "v1");
        Files.createDirectory(v1.toPath());

        VersionManager vm = new VersionManagerImpl(configFolder, null, null, true);

        assertThat(vm.getConfigurationVersionFolders()).containsExactly(v1);
        assertThat(vm.getConfigurationVersions()).containsExactly("v1");
        assertThat(vm.getVersionTimestamp()).isNotNull();
    }

    @Test
    public void constructorIgnoresTimestampFlag_withMultipleFolders() throws Exception {
        File v1 = new File(configFolder, "v1");
        Files.createDirectory(v1.toPath());
        File v2 = new File(configFolder, "v2");
        Files.createDirectory(v2.toPath());

        VersionManager vm = new VersionManagerImpl(configFolder, null, null, true);

        assertThat(vm.getConfigurationVersionFolders().size()).isEqualTo(2);
        assertThat(vm.getVersionTimestamp()).isNull();
    }
}
