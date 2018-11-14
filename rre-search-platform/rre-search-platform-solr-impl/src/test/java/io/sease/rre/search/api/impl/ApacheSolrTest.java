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
        assertFalse(platform.isSearchPlatformFile(dummyFile));
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenDirectoryNotContainSolrConfig() {
        assertFalse(platform.isSearchPlatformFile(tempFolder.getRoot()));
    }

    @Test
    public void isSearchPlatformFile_returnsTrueWhenDirectoryContainsSolrConfig() throws Exception {
        File configFile = tempFolder.newFile("solrconfig.xml");
        assertTrue(platform.isSearchPlatformFile(tempFolder.getRoot()));
    }
}
