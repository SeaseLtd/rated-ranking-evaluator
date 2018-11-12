package io.sease.rre.search.api.impl;

import io.sease.rre.search.api.SearchPlatform;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class ElasticsearchTest {

    @Rule
    public TemporaryFolder tempFolder = new TemporaryFolder();

    private SearchPlatform platform;

    @Before
    public void setupPlatform() {
        platform = new Elasticsearch();
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenDirectory() throws Exception {
        File dummyFile = tempFolder.newFolder();
        assertFalse(platform.isSearchPlatformFile(dummyFile));
    }

    @Test
    public void isSearchPlatformFile_returnsFalseWhenFileIsNotESConfig() throws Exception {
        File dummyFile = tempFolder.newFile();
        assertFalse(platform.isSearchPlatformFile(dummyFile));
    }

    @Test
    public void isSearchPlatformFile_returnsTrueWhenDirectoryContainsSolrConfig() throws Exception {
        File configFile = tempFolder.newFile("index-shape.json");
        assertTrue(platform.isSearchPlatformFile(configFile));
    }
}
