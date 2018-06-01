package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.JsonNode;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.Value;

import java.math.BigDecimal;
import java.util.Map;

import static io.sease.rre.Calculator.*;

public class AveragePrecision extends Metric {
    public final static String NAME = "AP";

    /**
     * Builds a new {@link AveragePrecision} metric.
     */
    public AveragePrecision() {
        super(NAME);
    }

    @Override
    public Value valueFactory() {

        return new Value(this) {
            private BigDecimal relevantItemsFound = BigDecimal.ZERO;

            private BigDecimal howManyRelevantDocuments = new BigDecimal(relevantDocuments.size());

            private BigDecimal value = BigDecimal.ZERO;
            private BigDecimal lastCollectedRecallLevel = BigDecimal.ZERO;

            @Override
            public void collect(final Map<String, Object> hit, final int rank, String version) {
                relevantItemsFound = sum(relevantItemsFound, judgment(id(hit)).isPresent() ? BigDecimal.ONE : BigDecimal.ZERO);

                final BigDecimal currentPrecision = divide(relevantItemsFound, new BigDecimal(rank));
                final BigDecimal currentRecall =
                        howManyRelevantDocuments.equals(BigDecimal.ZERO)
                                ? BigDecimal.ZERO
                                : divide(relevantItemsFound, howManyRelevantDocuments);
                value = sum(
                        value,
                        multiply(
                                currentPrecision,
                                subtract(currentRecall, lastCollectedRecallLevel)));

                lastCollectedRecallLevel = currentRecall;
            }

            @Override
            public BigDecimal value() {
                if (totalHits == 0) { return relevantDocuments.size() == 0 ? BigDecimal.ONE : BigDecimal.ZERO; }
                return value;
            }
        };
    }
}
