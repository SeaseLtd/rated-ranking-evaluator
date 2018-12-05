package io.sease.rre.server.controllers;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.Evaluation;
import io.sease.rre.server.domain.EvaluationMetadata;
import io.sease.rre.server.services.EvaluationHandlerService;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@RestController
public class RREController {
    private Evaluation evaluation = new Evaluation();
    private EvaluationMetadata metadata = new EvaluationMetadata(Collections.emptyList(), Collections.emptyList());

    @Autowired
    private EvaluationHandlerService evaluationHandler;

    @PostMapping("/evaluation")
    public void updateEvaluationData(@RequestBody final JsonNode requestBody) throws Exception {
        this.evaluation = evaluationHandler.processEvaluationRequest(requestBody);
        this.metadata = evaluationMetadata(evaluation);
    }

    public EvaluationMetadata getMetadata() {
        return metadata;
    }

    @ApiOperation(value = "Returns the evaluation data.")
    @ApiResponses(value = {
            @ApiResponse(code = 200, message = "Method successfully returned the evaluation data."),
            @ApiResponse(code = 400, message = "Bad Request"),
            @ApiResponse(code = 414, message = "Request-URI Too Long"),
            @ApiResponse(code = 500, message = "System internal failure occurred.")
    })
    @GetMapping(value = "/evaluation", produces = { "application/json" })
    @ResponseBody
    public Evaluation getEvaluationData() throws Exception {
        return evaluation;
    }

    /**
     * Creates the evaluation metadata.
     *
     * @param evaluation the evaluation data.
     * @return the evaluation metadata.
     */
    private EvaluationMetadata evaluationMetadata(final Evaluation evaluation) {
        final List<String> metrics = new ArrayList<>(
                evaluation.getChildren()
                        .iterator().next()
                        .getMetrics().keySet());

        final List<String> versions = new ArrayList<>(
                evaluation.getChildren()
                        .iterator().next()
                        .getMetrics().values().iterator().next().getVersions().keySet());

        return new EvaluationMetadata(versions, metrics);
    }
}
