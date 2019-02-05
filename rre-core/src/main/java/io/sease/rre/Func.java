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
package io.sease.rre;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.metrics.Metric;

import java.io.File;
import java.io.FileFilter;
import java.io.FilenameFilter;
import java.io.IOException;
import java.util.List;
import java.util.Optional;

import static io.sease.rre.Field.GAIN;
import static io.sease.rre.Field.RATING;
import static java.util.Collections.emptyList;
import static java.util.Optional.ofNullable;

/**
 * Shared functions / utilities.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class Func {
    public static final FilenameFilter ONLY_JSON_FILES = (dir, name) -> name.endsWith(".json");
    public static final FileFilter ONLY_DIRECTORIES = file -> file.isDirectory() && !file.isHidden();
    public static final FileFilter ONLY_NON_HIDDEN_FILES = file -> !file.isHidden();

    /**
     * Makes sure a non-null array is returned.
     * This is used in iterations, in order to avoid NPE.
     *
     * @param values the input array.
     * @param <T>    the array type.
     * @return the same array, if it's not null, an empty array otherwise.
     */
    public static <T> T[] safe(final T[] values) {
        return values != null ? values : emptyList().toArray(values);
    }

    /**
     * Makes sure a non-null array is returned.
     * This is used in iterations, in order to avoid NPE.
     *
     * @param values the input array.
     * @param <T>    the array type.
     * @return the same array, if it's not null, an empty array otherwise.
     */
    public static <T> List<T> safe(final List<T> values) {
        return values != null ? values : emptyList();
    }

    /**
     * Converts the content of the given file to a JSON node.
     *
     * @param file the input file.
     * @return a {@link JsonNode} instance representing the file content.
     */
    public static JsonNode toJson(final File file) {
        final ObjectMapper mapper = new ObjectMapper();
        try {
            return mapper.readTree(file);
        } catch (final IOException exception) {
            throw new IllegalArgumentException(file.getAbsolutePath(), exception);
        }
    }

    /**
     * Creates a new {@link Metric} instance.
     *
     * @param clazzName the metric class.
     * @return a new {@link Metric} instance.
     */
    @SuppressWarnings("unchecked")
    public static Class<? extends Metric> newMetricDefinition(final String clazzName) {
        try {
            return (Class<? extends Metric>) Class.forName(clazzName);
        } catch (final Exception exception) {
            throw new IllegalArgumentException(exception);
        }
    }

    /**
     * Returns the (child) node which declares the gain/rating associated with a given document.
     *
     * @param owner the owner (relevant) document.
     * @return the (child) node which declares the gain/rating associated with a given document.
     */
    public static Optional<JsonNode> gainOrRatingNode(final JsonNode owner) {
        return ofNullable(ofNullable(owner.get(GAIN)).orElse(owner.get(RATING)));
    }
}