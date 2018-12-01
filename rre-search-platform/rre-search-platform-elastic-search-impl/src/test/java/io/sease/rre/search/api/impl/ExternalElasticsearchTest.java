package io.sease.rre.search.api.impl;

import io.sease.rre.search.api.SearchPlatform;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class ExternalElasticsearchTest {

    private static final String INDEX_NAME = "test";

    @Rule
    public TemporaryFolder tempFolder = new TemporaryFolder();

    private SearchPlatform platform;

    @Before
    public void setupPlatform() {
        platform = new ExternalElasticsearch();
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenDirectory() throws Exception {
        File dummyFile = tempFolder.newFolder();
        assertFalse(platform.isSearchPlatformFile(INDEX_NAME, dummyFile));
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenFileIsNotESConfig() throws Exception {
        File dummyFile = tempFolder.newFile();
        assertFalse(platform.isSearchPlatformFile(INDEX_NAME, dummyFile));
    }

    @Test
    public void isSearchPlatformFile_returnsTrueWhenDirectoryContainsConfig() throws Exception {
        File configFile = tempFolder.newFile(ExternalElasticsearch.SETTINGS_FILE);
        assertTrue(platform.isSearchPlatformFile(INDEX_NAME, configFile));
    }
}
