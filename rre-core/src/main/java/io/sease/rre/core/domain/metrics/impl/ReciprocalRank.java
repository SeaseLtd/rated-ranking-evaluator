package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.core.domain.metrics.RankMetric;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;

/**
 * Reciprocal Rank metric
 *
 * @author agazzarini
 * @since 1.0
 */
public class ReciprocalRank extends RankMetric {
    /**
     * Builds a new ReciprocalRank at X metric.
     */
    public ReciprocalRank() {
        super("RR@10");
    }

    private int rank;
    private int maxGain;

    @Override
    public BigDecimal value() {
        if (totalHits == 0) { return hits.isEmpty() ? BigDecimal.ONE : BigDecimal.ZERO; }
        if (rank == 0) { return BigDecimal.ZERO;}

        return BigDecimal.ONE.divide(new BigDecimal(rank), 2, RoundingMode.HALF_UP);
    }

    @Override
    public void setRelevantDocuments(final JsonNode relevantDocuments) {
        super.setRelevantDocuments(relevantDocuments);
    }

    @Override
    public void collect(final Map<String, Object> hit, final int rank) {
        judgment(id(hit)).ifPresent(hitData -> {
            final int gain = hitData.get("gain").asInt();
            if (gain > maxGain) {
                this.rank = rank;
                this.maxGain = gain;
            }
        });
    }
}