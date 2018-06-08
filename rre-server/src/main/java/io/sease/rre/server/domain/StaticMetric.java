package io.sease.rre.server.domain;

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.Map;

import static java.util.Optional.ofNullable;

/**
 * A metric holder, which is not itself a metric but contains some metric data (actually name and value).
 * This is needed on RRE server side because here we no longer have the metrics definitions (in terms of classes / subclasses)
 * defined on the RRE core, but at the same time we need a general way to deserialize them in an object structure.
 *
 * @author agazzarini
 * @since 1.0
 */
public class StaticMetric extends Metric {

    /**
     * Builds a new {@link Metric} with the given mnemonic name.
     *
     * @param name the metric name.
     */
    public StaticMetric(final String name) {
        super(name);
    }

    public void collect(final String version, final BigDecimal value) {
        values.computeIfAbsent(version, v ->
                new ValueFactory(this) {
                    @Override
                    public BigDecimal value() {
                        return value;
                    }

                    @Override
                    public void collect(Map<String, Object> hit, int rank, String version) {
                        // Nothing to be done here...
                    }
                }
        );
    }

    @Override
    public ValueFactory valueFactory() {
        return new ValueFactory(this) {
            @Override
            public BigDecimal value() {
                return BigDecimal.TEN;
            }

            @Override
            public void collect(Map<String, Object> hit, int rank, String version) {
                // Nothing to be done here...
            }
        };
    }
}