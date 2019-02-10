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
     * @param fields    the fields to return.
     * @param maxRows   the maximum number of rows that will be returned.
     * @return the response of the query execution.
     */
    QueryOrSearchResponse executeQuery(String indexName, String query, final String[] fields, int maxRows);

    /**
     * Returns the name of this search platform.
     *
     * @return the name of this search platform.
     */
    String getName();

    /**
     * Does the platform require a refresh, outside of any concerns about
     * corpora updates, etc. This is likely to be true when the data directory
     * has been deleted, for example.
     *
     * @return {@code true} if the platform needs to be refreshed.
     */
    boolean isRefreshRequired();

    /**
     * Is the given file a search platform configuration container?
     * Ie. can it be used to initialise and/or configure a search platform
     * index?
     *
     * @param indexName the index name being processed.
     * @param file      the file to be tested.
     * @return {@code true} if the file is a search platform config file or
     * directory.
     */
    boolean isSearchPlatformFile(String indexName, File file);

    /**
     * @return {@code true} if this platform requires a corpora file to be
     * loaded in order to run.
     */
    boolean isCorporaRequired();
}
