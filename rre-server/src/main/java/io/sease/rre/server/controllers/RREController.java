package io.sease.rre.server.controllers;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.*;
import io.sease.rre.server.domain.EvaluationMetadata;
import io.sease.rre.server.domain.StaticMetric;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static java.util.stream.StreamSupport.stream;

@RestController
public class RREController {
    private Evaluation evaluation = new Evaluation();
    private EvaluationMetadata metadata = new EvaluationMetadata(Collections.emptyList(), Collections.emptyList());
    private ObjectMapper mapper = new ObjectMapper();

    @PostMapping("/evaluation")
    public void updateEvaluationData(@RequestBody final JsonNode evaluation) {
        this.evaluation = make(evaluation);

        metadata = evaluationMetadata(this.evaluation);
    }

    /**
     * Creates an evaluation object from the input JSON data.
     *
     * @param data the JSON payload.
     * @return a session evaluation instance.
     */
    private Evaluation make(final JsonNode data) {
        final Evaluation evaluation = new Evaluation();
        evaluation.setName(data.get("name").asText());

        metrics(data, evaluation);

        data.get("corpora").iterator().forEachRemaining(corpusNode -> {
            final String cname = corpusNode.get("name").asText();
            final Corpus corpus = evaluation.findOrCreate(cname, Corpus::new);

            metrics(corpusNode, corpus);

            corpusNode.get("topics").iterator().forEachRemaining(topicNode -> {
                final String tname = topicNode.get("name").asText();
                final Topic topic = corpus.findOrCreate(tname, Topic::new);
                metrics(topicNode, topic);

                topicNode.get("query-groups").iterator().forEachRemaining(groupNode -> {
                    final String gname = groupNode.get("name").asText();
                    final QueryGroup group = topic.findOrCreate(gname, QueryGroup::new);
                    metrics(groupNode, group);

                    groupNode.get("query-evaluations").iterator().forEachRemaining(queryNode -> {
                        final String qename = queryNode.get("query").asText();
                        final Query q = group.findOrCreate(qename, Query::new);
                        metrics(queryNode, q);


                        queryNode.get("results").fields().forEachRemaining(resultsEntry -> {
                            final MutableQueryOrSearchResponse versionedResponse =
                                    q.getResults().computeIfAbsent(
                                            resultsEntry.getKey(),
                                            version -> new MutableQueryOrSearchResponse());

                            JsonNode content = resultsEntry.getValue();
                            versionedResponse.setTotalHits(content.get("total-hits").asLong(), null);

                            stream(content.get("hits").spliterator(), false)
                                    .map(hit -> mapper.convertValue(hit, Map.class))
                                    .forEach(hit -> versionedResponse.collect(hit, -1, null));
                        });
                    });
                });
            });
        });

        return evaluation;
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
    @GetMapping("/evaluation")
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

    private void metrics(final JsonNode data, final DomainMember parent) {
        data.get("metrics").fields().forEachRemaining(entry -> {
            final StaticMetric metric = new StaticMetric(entry.getKey());

            entry.getValue().get("versions").fields().forEachRemaining(vEntry -> {
                metric.collect(vEntry.getKey(), new BigDecimal(vEntry.getValue().get("value").asDouble()).setScale(4, RoundingMode.CEILING));
            });
            parent.getMetrics().put(metric.getName(), metric);
        });
    }
}
