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
package io.sease.rre.maven.plugin.report.formats.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.maven.plugin.report.RREMavenReport;
import io.sease.rre.maven.plugin.report.domain.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.formats.OutputFormat;
import okhttp3.*;

import java.util.Locale;

import static java.util.Objects.requireNonNull;

/**
 * OutputFormat implementor for sending evaluation results to a running RRE Server instance.
 * Clearly, this assumes you're using an RRE Server somewhere.
 *
 * @author agazzarini
 * @since 1.0
 */
public class RREOutputFormat implements OutputFormat {
    @Override
    public void writeReport(final JsonNode data, final EvaluationMetadata metadata, final Locale locale, final RREMavenReport plugin) {
        try {
            final ObjectMapper serializer = new ObjectMapper();
            Request request = new Request.Builder()
                    .url(requireNonNull(HttpUrl.parse(plugin.getEndpoint() + "/evaluation")))
                    .post(RequestBody.create(MediaType.parse("application/json"), serializer.writeValueAsString(data)))
                    .build();

            try (final Response response = new OkHttpClient().newCall(request).execute()) {
                if (response.code() != 200) {
                    plugin.getLog().error("Exception while communicating with RREServer. Return code was: " + response.code());
                } else {
                    plugin.getLog().info("Evaluation data has been correctly sent to RRE Server located at " + plugin.getEndpoint());
                }
            }
        } catch (final Exception exception) {
            plugin.getLog().error("RRE: Unable to connect to RRE Server. See below for further details.", exception);
        }
    }
}
