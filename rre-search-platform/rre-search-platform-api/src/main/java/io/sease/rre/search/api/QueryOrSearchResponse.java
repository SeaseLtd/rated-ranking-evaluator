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

import java.util.List;
import java.util.Map;

import static java.util.Collections.unmodifiableList;

/**
 * This is the result of a query / search execution.
 *
 * @author agazzarini
 * @since 1.0
 */
public class QueryOrSearchResponse {
    private final long totalHits;
    private final List<Map<String, Object>> hits;

    /**
     * Builds a new response with the given data.
     *
     * @param totalHits the total hits of this response.
     * @param hits      the current hits window.
     */
    public QueryOrSearchResponse(final long totalHits, final List<Map<String, Object>> hits) {
        this.totalHits = totalHits;
        this.hits = unmodifiableList(hits);
    }

    /**
     * Returns the total hits number associated with this response.
     *
     * @return the total hits number associated with this response.
     */
    public long totalHits() {
        return totalHits;
    }

    /**
     * Returns the current hits window.
     *
     * @return the current hits window.
     */
    public List<Map<String, Object>> hits() {
        return hits;
    }
}