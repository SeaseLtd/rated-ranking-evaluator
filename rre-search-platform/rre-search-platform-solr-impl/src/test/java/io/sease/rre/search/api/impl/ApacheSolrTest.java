package io.sease.rre.search.api.impl;

import io.sease.rre.search.api.SearchPlatform;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class ApacheSolrTest {

    private static final String INDEX_NAME = "test";

    @Rule
    public TemporaryFolder tempFolder = new TemporaryFolder();

    private SearchPlatform platform;

    @Before
    public void setupPlatform() {
        platform = new ApacheSolr();
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenNotDirectory() throws Exception {
        File dummyFile = tempFolder.newFile();
        assertFalse(platform.isSearchPlatformFile(INDEX_NAME, dummyFile));
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenDirectoryNotContainSolrConfig() {
        assertFalse(platform.isSearchPlatformFile(INDEX_NAME, tempFolder.getRoot()));
    }

    @Test
    public void isSearchPlatformFile_returnsTrueWhenDirectoryContainsSolrConfig() throws Exception {
        File configFile = tempFolder.newFolder(INDEX_NAME);
        assertTrue(platform.isSearchPlatformFile(INDEX_NAME, configFile));
    }
}
