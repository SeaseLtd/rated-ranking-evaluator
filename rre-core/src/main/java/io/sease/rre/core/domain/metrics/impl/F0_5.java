package io.sease.rre.core.domain.metrics.impl;

/**
 * A F-measure which weighs recall lower than precision (by attenuating the influence of false negatives).
 *
 * @author agazzarini
 * @since 1.0
 */
public class F0_5 extends FMeasure {
    /**
     * Builds a new F1 metric instance.
     */
    public F0_5() {
        super("F0.5", 0.5f);
    }
}
