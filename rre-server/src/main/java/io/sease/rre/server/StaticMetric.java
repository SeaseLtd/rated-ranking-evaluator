package io.sease.rre.server;

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.Map;

public class StaticMetric extends Metric {
    private BigDecimal value;

    /**
     * Builds a new {@link Metric} with the given mnemonic name.
     *
     * @param name the metric name.
     */
    public StaticMetric(final String name) {
        super(name);
    }

    public void setValue(final BigDecimal value) {
        this.value = value;
    }

    @Override
    public ValueFactory valueFactory() {
        return new ValueFactory(this) {
            @Override
            public BigDecimal value() {
                return value;
            }

            @Override
            public void collect(Map<String, Object> hit, int rank, String version) {
                // Nothing to be done here...
            }
        };
    }
}