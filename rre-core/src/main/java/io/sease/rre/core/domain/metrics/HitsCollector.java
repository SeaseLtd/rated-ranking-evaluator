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
package io.sease.rre.core.domain.metrics;

import java.util.Map;

/**
 * An object which collects search hits through an iterative process.
 * The concrete implementor declares an interface who allows to be notified
 * when a given search hit is made available.
 *
 * @author agazzarini
 * @since 1.0
 */
public interface HitsCollector {
    /**
     * Consumes the "hit availability" event.
     *
     * @param hit  the search hit.
     * @param rank the hit rank.
     */
    void collect(Map<String, Object> hit, int rank, String version);

    /**
     * Sets the total hits (i.e. the total number of results) of the query response associated with this metric.
     *
     * @param totalHits the total hits of the query response associated with this metric.
     */
    void setTotalHits(long totalHits, String version);
}