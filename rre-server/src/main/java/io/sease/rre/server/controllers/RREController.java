package io.sease.rre.server.controllers;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.Evaluation;
import io.sease.rre.server.EvaluationMetadata;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@RestController
public class RREController extends BaseController {
    private Evaluation evaluation = new Evaluation();
    private EvaluationMetadata metadata = new EvaluationMetadata(Collections.emptyList(), Collections.emptyList());

    @PostMapping("/evaluation")
    public void updateEvaluationData(@RequestBody final Evaluation evaluation) {
        this.evaluation = evaluation;
        metadata = evaluationMetadata(this.evaluation);
    }

    public EvaluationMetadata getMetadata() {
        return metadata;
    }

    @GetMapping("/evaluation")
    public Evaluation getEvaluationData() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        return mapper.readValue(new FileReader(new File("/Users/agazzarini/IdeaProjects/rated-ranking-evaluator/rre-maven-plugin/rre-maven-solr-plugin/target/rre/evaluation.json")), Evaluation.class);
        //return evaluation;
    }

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
