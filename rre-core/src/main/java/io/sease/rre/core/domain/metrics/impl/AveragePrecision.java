package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.core.domain.metrics.RankMetric;

import java.math.BigDecimal;
import java.util.Map;

import static io.sease.rre.Calculator.*;

public class AveragePrecision extends RankMetric {
    private BigDecimal relevantItemsFound;

    private BigDecimal howManyRelevantDocuments;

    private BigDecimal value = BigDecimal.ZERO;
    private BigDecimal lastCollectedRecallLevel = BigDecimal.ZERO;

    /**
     * Builds a new {@link AveragePrecision} metric.
     */
    public AveragePrecision() {
        super("AP");
    }

    @Override
    public void collect(final Map<String, Object> hit, final int rank) {
        relevantItemsFound = sum(relevantItemsFound, judgment(id(hit)).isPresent() ? BigDecimal.ONE : BigDecimal.ZERO);

        final BigDecimal currentPrecision = divide(relevantItemsFound, new BigDecimal(rank));
        final BigDecimal currentRecall = divide(relevantItemsFound, howManyRelevantDocuments);
        value = sum(
                    value,
                    multiply(
                            currentPrecision,
                            subtract(currentRecall, lastCollectedRecallLevel)));

        lastCollectedRecallLevel = currentRecall;
    }

    @Override
    public BigDecimal value() {
        return value;
    }

    @Override
    public void setRelevantDocuments(final JsonNode relevantDocuments) {
        super.setRelevantDocuments(relevantDocuments);
        this.howManyRelevantDocuments = new BigDecimal(relevantDocuments.size());
    }
}
