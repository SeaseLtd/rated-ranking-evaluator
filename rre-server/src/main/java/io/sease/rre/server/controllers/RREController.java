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

    @Autowired
    private EvaluationHandlerService evaluationHandler;

    @PostMapping("/evaluation")
    public void updateEvaluationData(@RequestBody final JsonNode requestBody) throws Exception {
        evaluationHandler.processEvaluationRequest(requestBody);
    }

    public EvaluationMetadata getMetadata() {
        return evaluationHandler.getEvaluationMetadata();
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
    public Evaluation getEvaluationData() {
        return evaluationHandler.getEvaluation();
    }
}
