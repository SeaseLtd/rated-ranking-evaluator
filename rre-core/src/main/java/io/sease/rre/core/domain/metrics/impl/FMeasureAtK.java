package io.sease.rre.core.domain.metrics.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.sease.rre.Calculator;
import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * The F-measure measures the effectiveness of retrieval with respect to a user who attaches (beta) times as much importance to recall as precision.
 * In statistical analysis of binary classification, the F1 score (also F-score or F-measure) is a measure of a test's accuracy.
 * It considers both the precision p and the recall r of the test to compute the score: p is the number of correct positive results
 * divided by the number of all positive results returned by the classifier, and r is the number of correct positive results
 * divided by the number of all relevant samples (all samples that should have been identified as positive).
 *
 * The F1 score is the harmonic average of the precision and recall, where an F1 score reaches its best value at 1
 * (perfect precision and recall) and worst at 0.
 *
 * (Wikipedia)
 *
 * @author agazzarini
 * @author worleydl 
 */
public class FMeasureAtK extends Metric {

    private final BigDecimal beta;
    private final int k;

    final Metric precision;
    final Metric recall;

    /**
     * Builds a new F-Measure/F-Score at K metric with the given beta factor.
     *
     * @param beta the balance factor between precision and recall.
     * @param k the measure bound
     */
    public FMeasureAtK(@JsonProperty("beta") final float beta, @JsonProperty("k") final int k) {
        super("F" + beta + "@" + k);
        this.beta = BigDecimal.valueOf(beta).pow(2);
        this.k = k;
        
        this.precision = new PrecisionAtK(k);
        this.recall = new RecallAtK(k);
    }

    @Override
    public ValueFactory createValueFactory(final String version) {
        return new ValueFactory(this, version) {
            @Override
            public BigDecimal value() {
                final BigDecimal betaPlusOne = Calculator.sum(BigDecimal.ONE, beta);

                final BigDecimal p = precision.valueFactory(version).value();
                final BigDecimal r = recall.valueFactory(version).value();

                if (p.doubleValue() == 0 || r.doubleValue() == 0) return BigDecimal.ZERO;

                final BigDecimal precisionTimesBeta = Calculator.multiply(p, beta);

                final BigDecimal dividend = Calculator.multiply(p,r);
                final BigDecimal divisor = Calculator.sum(precisionTimesBeta,r);

                return Calculator.multiply(betaPlusOne, Calculator.divide(dividend, divisor));
            }

            @Override
            public void setTotalHits(long totalHits, String version) {
                precision.setTotalHits(totalHits, version);
                recall.setTotalHits(totalHits, version);
            }

            @Override
            public void collect(final Map<String, Object> hit, final int rank, final String version) {
                precision.collect(hit, rank, version);
                recall.collect(hit, rank, version);
            }
        };
    }

    @Override
    public void setTotalHits(long totalHits, String version) {
        super.setTotalHits(totalHits, version);
    }

    @Override
    public void setRelevantDocuments(JsonNode relevantDocuments) {
        super.setRelevantDocuments(relevantDocuments);
        precision.setRelevantDocuments(relevantDocuments);
        recall.setRelevantDocuments(relevantDocuments);
    }

    @Override
    public void setVersions(List<String> versions) {
        super.setVersions(versions);
        precision.setVersions(versions);
        recall.setVersions(versions);
    }

    @Override
    public void setIdFieldName(String idFieldName) {
        super.setIdFieldName(idFieldName);
        precision.setIdFieldName(idFieldName);
        recall.setIdFieldName(idFieldName);
    }

    @Override
    public int getRequiredResults() {
        return k;
    }
}
