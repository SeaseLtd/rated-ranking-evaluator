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
package io.sease.rre.maven.plugin.report.domain;

import java.util.List;

/**
 * Basic metadata about an evaluation result.
 *
 * @author agazzarini
 * @since 1.0
 */
public class EvaluationMetadata {
    public final List<String> versions;
    public final List<String> metrics;

    /**
     * Builds a new metadata with the given values.
     *
     * @param versions the available versions in the evaluation data.
     * @param metrics  the available metrics in the evaluation data.
     */
    public EvaluationMetadata(final List<String> versions, final List<String> metrics) {
        this.versions = versions;
        this.metrics = metrics;
    }

    /**
     * Returns the total number of versions used in this evaluation cycle.
     *
     * @return the total number of versions used in this evaluation cycle.
     */
    public int howManyVersions() {
        return versions.size();
    }

    /**
     * Returns the total number of metrics used in this evaluation cycle.
     *
     * @return the total number of metrics used in this evaluation cycle.
     */
    public int howManyMetrics() {
        return metrics.size();
    }
}