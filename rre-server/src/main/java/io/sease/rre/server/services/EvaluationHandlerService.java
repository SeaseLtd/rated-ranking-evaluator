package io.sease.rre.server.services;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.core.domain.Evaluation;
import org.springframework.stereotype.Service;

/**
 * An EvaluationHandlerService can be used to process an incoming evaluation
 * update request. It should extract the relevant details from the request,
 * and use them to build an Evaluation object that can be used to populate
 * the dashboard.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
@Service
public interface EvaluationHandlerService {

    /**
     * Update the currently held evaluation data.
     *
     * @param requestData incoming data giving details of evaluation.
     * @throws Exception if the data cannot be processed.
     */
    Evaluation processEvaluationRequest(final JsonNode requestData) throws Exception;
}
