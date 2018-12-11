package io.sease.rre.persistence.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.domain.*;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.impl.Precision;
import io.sease.rre.core.domain.metrics.impl.Recall;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import java.util.*;

import static java.util.stream.Collectors.toList;
import static org.assertj.core.api.Assertions.assertThat;

/**
 * Unit tests for the query version report class.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class QueryVersionReportTest {

    private static Evaluation evaluation;

    private Query firstQuery;

    @BeforeClass
    public static void setupEvaluation() throws Exception {
        JsonNode relevantDocs = new ObjectMapper().readTree("{\"1\": { \"gain\": 3 }," +
                "\"2\": { \"gain\": 3 } }");
        List<Class<? extends Metric>> metricClasses = Arrays.asList(Precision.class, Recall.class);
        List<Metric> metrics = metricClasses.stream()
                .map(def -> {
                    try {
                        final Metric metric = def.newInstance();
                        metric.setIdFieldName("_id");
                        metric.setRelevantDocuments(relevantDocs);
                        metric.setVersions(Arrays.asList("1.0", "1.1"));
                        return metric;
                    } catch (final Exception exception) {
                        throw new IllegalArgumentException(exception);
                    }
                })
                .collect(toList());

        evaluation = new Evaluation();
        Corpus c = evaluation.findOrCreate("corpus", Corpus::new);
        Topic t = c.findOrCreate("topic", Topic::new);
        QueryGroup qg = t.findOrCreate("group", QueryGroup::new);

        Map<String, Object> result1 = new HashMap<>();
        result1.put("_id", "1");
        Map<String, Object> result2 = new HashMap<>();
        result2.put("_id", "2");

        Query q = qg.findOrCreate("query1", Query::new);
        q.collect(result1, 1, "1.0");
        q.collect(result2, 2, "1.0");
        q.setTotalHits(2, "1.0");
        q.collect(result2, 1, "1.1");
        q.collect(result2, 2, "1.1");
        q.setTotalHits(2, "1.1");
        q.setIdFieldName("_id");
        q.setRelevantDocuments(relevantDocs);
        q.prepare(metrics);
        q.notifyCollectedMetrics();
    }

    @Before
    public void extractFirstQuery() {
        firstQuery = evaluation.getChildren().get(0)     // Corpus
                .getChildren().get(0)                   // Topic
                .getChildren().get(0)                   // QueryGroup
                .getChildren().get(0);
    }

    @Test
    public void canConvertQueries() {
        List<QueryVersionReport> queryVersions = QueryVersionReport.fromQuery(firstQuery);

        assertThat(queryVersions.size()).isEqualTo(2);

        QueryVersionReport qvr = queryVersions.get(0);
        assertThat(qvr.getCorpora()).isEqualTo("corpus");
        assertThat(qvr.getTopic()).isEqualTo("topic");
        assertThat(qvr.getQueryGroup()).isEqualTo("group");
        assertThat(qvr.getQueryText()).isEqualTo("query1");
        assertThat(qvr.getVersion()).isEqualTo("1.0");
        assertThat(qvr.getMetrics().size()).isEqualTo(2);
        assertThat(qvr.getMetricValues().size()).isEqualTo(2);
        assertThat(qvr.getMetricValues()).containsKeys("p", "r");
    }
}
