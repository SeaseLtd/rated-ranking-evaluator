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
package io.sease.rre.server.services;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.core.domain.Evaluation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * Implementation of the evaluation handler that extracts a URL from the
 * evaluation update request, and uses that as the endpoint from which the
 * evaluation data should be read.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
@Service
@Profile("url")
public class URLEvaluationHandlerService extends HttpEvaluationHandlerService implements EvaluationHandlerService {

    private static final Logger LOGGER = LoggerFactory.getLogger(URLEvaluationHandlerService.class);

    private URLEvaluationUpdater updater = null;

    @Override
    public void processEvaluationRequest(JsonNode requestData) throws EvaluationHandlerException {
        try {
            if (updater != null && updater.isAlive()) {
                throw new EvaluationHandlerException("Update is already running - request rejected!");
            }

            final String urlParam = requestData.get("url").asText();
            LOGGER.debug("Extracted URL {} from incoming request", urlParam);

            // Build the evaluation in a separate thread - avoid causing timeouts in the report plugin
            updater = createUpdaterThread(new URL(urlParam));
            updater.start();
        } catch (IOException e) {
            LOGGER.error("Caught IOException processing request: {}", e.getMessage());
            throw new EvaluationHandlerException(e);
        }
    }

    private URLEvaluationUpdater createUpdaterThread(URL evaluationUrl) {
        URLEvaluationUpdater thread = new URLEvaluationUpdater(evaluationUrl);
        // Run the thread in the background
        thread.setDaemon(true);
        return thread;
    }


    class URLEvaluationUpdater extends Thread {

        private final URL evaluationUrl;

        URLEvaluationUpdater(URL evaluationUrl) {
            this.evaluationUrl = evaluationUrl;
        }

        @Override
        public void run() {
            try {
                LOGGER.info("Building evaluation from URL {}", evaluationUrl);
                final JsonNode evaluationNode = readNodeFromUrl(evaluationUrl);
                setEvaluation(make(evaluationNode));
                LOGGER.debug("Evaluation build complete");
            } catch (IOException e) {
                LOGGER.error("Caught IOException building evaluation: {}", e.getMessage());
            }
        }

        private JsonNode readNodeFromUrl(URL evaluationUrl) throws IOException {
            try {
                return getMapper().readTree(evaluationUrl);
            } catch (IOException e) {
                LOGGER.error("Caught IOException reading JSON from {}: {}", evaluationUrl, e.getMessage());
                throw e;
            }
        }
    }
}
