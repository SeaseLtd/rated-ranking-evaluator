package io.sease.rre.maven.plugin.search;

import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;

import java.io.File;
import java.util.Map;

/**
 * A dummy search platform implementation for testing the Evaluation Mojo.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class ArgConstructorSearchPlatform implements SearchPlatform {

    public ArgConstructorSearchPlatform(String dummyText) {

    }

    @Override
    public void beforeStart(Map<String, Object> configuration) {

    }

    @Override
    public void load(File dataToBeIndexed, File configFolder, String collection, String version) {

    }

    @Override
    public void start() {

    }

    @Override
    public void afterStart() {

    }

    @Override
    public void beforeStop() {

    }

    @Override
    public QueryOrSearchResponse executeQuery(String collection, String version, String query, String[] fields, int maxRows) {
        return null;
    }

    @Override
    public String getName() {
        return null;
    }

    @Override
    public boolean isRefreshRequired() {
        return false;
    }

    @Override
    public boolean isSearchPlatformConfiguration(String indexName, File file) {
        return false;
    }

    @Override
    public boolean isCorporaRequired() {
        return false;
    }

    @Override
    public void close() {
    }

    @Override
    public boolean checkCollection(String collection, String version) {
        return true;
    }
}
