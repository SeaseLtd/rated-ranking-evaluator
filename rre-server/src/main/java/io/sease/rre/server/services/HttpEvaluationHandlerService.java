package io.sease.rre.server.services;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.*;
import io.sease.rre.server.domain.EvaluationMetadata;
import io.sease.rre.server.domain.StaticMetric;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static java.util.stream.StreamSupport.stream;

/**
 * Implementation of the evaluation manager service which will extract a
 * complete Evaluation object from the request data.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
@Service
@Profile({"http", "default"})
public class HttpEvaluationHandlerService implements EvaluationHandlerService {

    private final ObjectMapper mapper = new ObjectMapper();

    private Evaluation evaluation = new Evaluation();
    private EvaluationMetadata metadata = new EvaluationMetadata(Collections.emptyList(), Collections.emptyList());

    @Override
    public void processEvaluationRequest(final JsonNode requestData) throws EvaluationHandlerException {
        evaluation = make(requestData);
    }

    @Override
    public Evaluation getEvaluation() {
        return evaluation;
    }

    @Override
    public EvaluationMetadata getEvaluationMetadata() {
        return metadata;
    }

    void setEvaluation(Evaluation eval) {
        this.evaluation = eval;
        this.metadata = extractEvaluationMetadata(eval);
    }

    ObjectMapper getMapper() {
        return mapper;
    }

    /**
     * Creates an evaluation object from the input JSON data.
     *
     * @param data the JSON payload.
     * @return a session evaluation instance.
     */
    protected Evaluation make(final JsonNode data) {
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

    private void metrics(final JsonNode data, final DomainMember parent) {
        data.get("metrics").fields().forEachRemaining(entry -> {
            final StaticMetric metric = new StaticMetric(entry.getKey());

            entry.getValue().get("versions").fields().forEachRemaining(vEntry -> {
                metric.collect(vEntry.getKey(), new BigDecimal(vEntry.getValue().get("value").asDouble()).setScale(4, RoundingMode.CEILING));
            });
            parent.getMetrics().put(metric.getName(), metric);
        });
    }

    /**
     * Extract the evaluation metadata from an evaluation.
     *
     * @param evaluation the evaluation data.
     * @return the evaluation metadata.
     */
    public static EvaluationMetadata extractEvaluationMetadata(final Evaluation evaluation) {
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
