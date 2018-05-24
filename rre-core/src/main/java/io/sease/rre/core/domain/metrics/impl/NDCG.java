package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.core.domain.metrics.RankMetric;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.StreamSupport;

import static java.util.Collections.emptyList;
import static java.util.stream.Collectors.groupingBy;

public class NDCG extends RankMetric {
    private BigDecimal dcg = BigDecimal.ZERO;

    /**
     * Builds a new NDCG metric.
     */
    public NDCG() {
        super("NDCG");
    }

    @Override
    public void collect(final Map<String, Object> hit, final int rank) {
        judgment(id(hit))
                .ifPresent(judgment -> {
                    switch(rank) {
                        case 1:
                            dcg = judgment.get("gain").decimalValue();
                            break;
                        default:
                            final double gain = judgment.get("gain").doubleValue();
                            dcg = dcg.add(new BigDecimal(gain / (Math.log(rank) / Math.log(2))));
                    }
                });
    }

    @Override
    public BigDecimal value() {
        if (totalHits == 0) { return hits.isEmpty() ? BigDecimal.ONE : BigDecimal.ZERO; }

        return dcg.divide(idealDcg(relevantDocuments), 2, RoundingMode.FLOOR);
    }

    private BigDecimal idealDcg(final JsonNode relevantDocuments) {
        final int windowSize = Math.min(relevantDocuments.size(), 10);
        final int [] gains = new int [windowSize];

        final Map<Integer, List<JsonNode>> groups = StreamSupport.stream(relevantDocuments.spliterator(), false).collect(groupingBy(doc -> doc.get("gain").asInt()));

        final int veryRelevantDocsCount= groups.getOrDefault(2, emptyList()).size();
        final int howManyVeryRelevantDocs = Math.min(veryRelevantDocsCount, windowSize);

        final int marginallyRelevantDocsCount = groups.getOrDefault(1, emptyList()).size();
        final int howManyMarginallyRelevantDocs = Math.max(Math.min(marginallyRelevantDocsCount - howManyVeryRelevantDocs, 0), 0);

        Arrays.fill(gains, 0, howManyVeryRelevantDocs, 2);
        if (howManyVeryRelevantDocs < windowSize) {
            Arrays.fill(gains, howManyVeryRelevantDocs, howManyVeryRelevantDocs + Math.min((windowSize - howManyVeryRelevantDocs), howManyMarginallyRelevantDocs), 1);
        }

        BigDecimal result = new BigDecimal(gains[0]);
        for (int i = 1 ; i < gains.length; i++) {
            result = result.add(new BigDecimal(gains[i] / (Math.log(i + 1) / Math.log(2))));
        }

        return result;
    }
}
