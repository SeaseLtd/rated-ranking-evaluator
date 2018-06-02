package io.sease.rre.core.domain.metrics.impl;

import io.sease.rre.core.domain.metrics.Metric;
import io.sease.rre.core.domain.metrics.ValueFactory;

import java.math.BigDecimal;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static io.sease.rre.Calculator.divide;
import static io.sease.rre.Calculator.sum;

public class AveragedMetric extends Metric {
    class MutableValueFactory extends ValueFactory {
        private BigDecimal value = BigDecimal.ZERO;
        private final AtomicInteger counter = new AtomicInteger(1);

        /**
         * Builds a new (Metric) valueFactory with the given (metric) owner.
         *
         * @param owner the owner metric.
         */
        protected MutableValueFactory(final Metric owner) {
            super(owner);
        }

        @Override
        public BigDecimal value() {
            return value;
        }

        public void collect(final BigDecimal additionalValue) {
            value = divide(sum(value, additionalValue), counter.incrementAndGet());
        }

        @Override
        public void collect(final Map<String, Object> hit, final int rank, final String version) {
            // Noop
        }
    }

    public AveragedMetric(final String name) {
        super(name);
    }

    public void collect(final String version, final BigDecimal additionalValue) {
        final MutableValueFactory valueFactory = (MutableValueFactory) values.computeIfAbsent(version, v ->  valueFactory());
        valueFactory.collect(additionalValue);
    }

    @Override
    public ValueFactory valueFactory() {
        return new MutableValueFactory(this);
    }
}