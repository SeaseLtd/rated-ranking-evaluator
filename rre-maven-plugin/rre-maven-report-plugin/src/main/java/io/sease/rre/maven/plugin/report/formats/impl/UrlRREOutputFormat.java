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
import io.sease.rre.maven.plugin.report.RREMavenReport;
import io.sease.rre.maven.plugin.report.domain.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.formats.OutputFormat;
import okhttp3.*;

import java.io.File;
import java.util.Locale;

import static java.util.Objects.requireNonNull;

/**
 * RRE server implementation of OutputFormat that sends a file URL to the
 * server, rather than bundling the whole evaluation output in one request.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class UrlRREOutputFormat implements OutputFormat {

    @Override
    public void writeReport(JsonNode data, EvaluationMetadata metadata, Locale locale, RREMavenReport plugin) {
        try {
            Request request = new Request.Builder()
                    .url(requireNonNull(HttpUrl.parse(plugin.getEndpoint() + "/evaluation")))
                    .post(RequestBody.create(MediaType.parse("application/json"),
                            "{ \"url\": \"" + new File(plugin.getEvaluationFile()).toURI().toURL() + "\" }"))
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
