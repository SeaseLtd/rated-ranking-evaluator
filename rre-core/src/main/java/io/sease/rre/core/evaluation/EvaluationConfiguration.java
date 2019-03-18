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
package io.sease.rre.core.evaluation;

/**
 * Configuration for the evaluation process. The values set here will define
 * which {@link EvaluationManager} implementation is returned by the
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class EvaluationConfiguration {

    /**
     * Default configuration, with async enabled for evaluations but not
     * queries, threadpool size 4.
     */
    public static EvaluationConfiguration DEFAULT_CONFIG = defaultConfiguration();

    private boolean runAsync = true;
    private boolean runQueriesAsync = false;
    private int threadpoolSize = 4;

    @SuppressWarnings("unused")
    public EvaluationConfiguration() {
        // Do nothing - required for Maven initialisation
    }

    private EvaluationConfiguration(boolean async, boolean qAsync, int threadpool) {
        this.runAsync = async;
        this.runQueriesAsync = qAsync;
        this.threadpoolSize = threadpool;
    }

    /**
     * Running asynchronously should reduce the time required to evaluate all
     * of the queries, if multi-threading is available.
     *
     * @return {@code true} if evaluations should be run asynchnronously.
     */
    public boolean isRunAsync() {
        return runAsync;
    }

    /**
     * Each evaluation consists of one or more versioned queries, which may
     * be run asynchronously. Note that this may not reduce the time required
     * to run, and in some cases can increase it.
     *
     * @return {@code true} if individual queries should be run asynchronously.
     */
    public boolean isRunQueriesAsync() {
        return runQueriesAsync;
    }

    /**
     * @return the size of the threadpool to use for evaluations.
     */
    public int getThreadpoolSize() {
        return threadpoolSize;
    }

    private static EvaluationConfiguration defaultConfiguration() {
        return new EvaluationConfiguration(true, false, 4);
    }
}
