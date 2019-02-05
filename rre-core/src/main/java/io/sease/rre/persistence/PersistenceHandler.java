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
package io.sease.rre.persistence;

import io.sease.rre.core.domain.Query;

import java.util.Map;

/**
 * A persistence handler can be used to record the output from all queries
 * run during an evaluation.
 * <p>
 * Exceptions during processing are expected to be handled internally.
 * Exceptions thrown during the {@link #beforeStart()} and {@link #start()}
 * stages may be passed up the stack, to alert the PersistenceManager that
 * the handler could not be started for some reason, and should not be used.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public interface PersistenceHandler {

    /**
     * Configure the persistence handler implementation.
     *
     * @param name          the name given to the handler in the main configuration.
     * @param configuration the configuration parameters specific to the
     *                      handler.
     */
    void configure(String name, Map<String, Object> configuration);

    /**
     * @return the configuration name for this handler instance.
     */
    String getName();

    /**
     * Execute any necessary tasks required to initialise the handler.
     *
     * @throws PersistenceException if any pre-start checks fail. This should
     *                              be used to report breaking failures - eg. issues that will stop the
     *                              handler from starting.
     */
    void beforeStart() throws PersistenceException;

    /**
     * Execute any necessary start-up tasks.
     *
     * @throws PersistenceException if the handler cannot be started for any
     *                              reason.
     */
    void start() throws PersistenceException;

    /**
     * Record a query.
     *
     * @param q the query.
     */
    void recordQuery(Query q);

    /**
     * Execute any tasks necessary before stopping - for example, writing out
     * buffered content.
     */
    void beforeStop();

    /**
     * Execute any necessary shutdown tasks - for example, closing output
     * streams.
     */
    void stop();
}
