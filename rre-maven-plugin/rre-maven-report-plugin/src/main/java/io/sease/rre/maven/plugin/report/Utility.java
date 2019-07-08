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
package io.sease.rre.maven.plugin.report;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.stream.Stream;
import java.util.stream.StreamSupport;

import static java.util.Optional.ofNullable;

/**
 * Shared utilities.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class Utility {
    /**
     * Returns the input JSON payload as a pretty formatted string.
     *
     * @param payload the JSON object.
     * @return the input JSON payload as a pretty formatted string.
     */
    public static String pretty(final JsonNode payload) {
        try {
            final ObjectMapper mapper = new ObjectMapper();
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(mapper.readTree(payload.asText()));
        } catch (final Exception exception) {
            return payload.asText();
        }
    }

    /**
     * Produces a stream consisting of all children of the given JSON node.
     *
     * @param parent the JSON node.
     * @param name   the name of the attribute associated with the requested children.
     * @return a stream consisting of all children of the given JSON node.
     */
    public static Stream<JsonNode> all(final JsonNode parent, final String name) {
        return ofNullable(parent.get(name))
                .map(node -> StreamSupport.stream(parent.get(name).spliterator(), false))
                .orElseGet(Stream::empty);
    }
}