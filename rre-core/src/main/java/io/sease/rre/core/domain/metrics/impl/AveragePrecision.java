package io.sease.rre.core.domain.metrics.impl;

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.Map;

import static io.sease.rre.Calculator.*;

public class AveragePrecision extends Metric {
    /**
     * Builds a new {@link AveragePrecision} metric.
     */
    public AveragePrecision() {
        super("AP");
    }

    @Override
    public ValueFactory valueFactory() {

        return new ValueFactory(this) {
            private BigDecimal relevantItemsFound = BigDecimal.ZERO;

            private BigDecimal howManyRelevantDocuments;

            private BigDecimal value = BigDecimal.ZERO;
            private BigDecimal lastCollectedRecallLevel = BigDecimal.ZERO;

            @Override
            public void collect(final Map<String, Object> hit, final int rank, String version) {
                if (howManyRelevantDocuments == null)
                    howManyRelevantDocuments = new BigDecimal(relevantDocuments.size());

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
                if (relevantDocuments.size() == 0) {
                    return totalHits == 0 ? BigDecimal.ONE : BigDecimal.ZERO;
                }
                return value;
            }
        };
    }
}
