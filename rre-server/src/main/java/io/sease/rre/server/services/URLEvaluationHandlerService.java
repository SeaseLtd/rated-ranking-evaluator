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

    @Override
    public Evaluation processEvaluationRequest(JsonNode requestData) {
        Evaluation eval = new Evaluation();

        try {
            final String urlParam = requestData.get("url").asText();
            final JsonNode evaluationNode = readNodeFromUrl(new URL(urlParam));

            eval = make(evaluationNode);
        } catch (IOException e) {
            LOGGER.error("Caught IOException processing request: {}", e.getMessage());
        }

        return eval;
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
