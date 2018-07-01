package io.sease.rre.search.api;

import java.io.Closeable;
import java.io.File;
import java.util.Map;

/**
 * A supertype layer interface for denoting the behaviour expected by a given search platform.
 * A behaviour in this perspective means all lifecycle API methods needed for controlling and interacting with
 * a given search engine instance.
 *
 * @author agazzarini
 * @since 1.0
 */
public interface SearchPlatform extends Closeable {
    /**
     * Starts this search platform.
     *
     * @param configuration the platform configuration.
     */
    void beforeStart(Map<String, Object> configuration);

    /**
     * Loads some data in a given index.
     *
     * @param corpus          the data.
     * @param configFolder    the folder that contains the configuration for the given index.
     * @param targetIndexName the name of the index where data will be indexed.
     */
    void load(final File corpus, final File configFolder, final String targetIndexName);

    /**
     * Starts this search platform.
     */
    void start();

    /**
     * Initialises this search platform.
     */
    void afterStart();

    /**
     * Releases any resource.
     */
    void beforeStop();

    /**
     * Executes the given query.
     * The semantic of the input query may change between concrete platforms
     *
     * @param indexName the index name that holds the data.
     * @param query     the query.
     * @param maxRows   the maximum number of rows that will be returned.
     * @return the response of the query execution.
     */
    QueryOrSearchResponse executeQuery(String indexName, String query, final String[] fields, int maxRows);
}
