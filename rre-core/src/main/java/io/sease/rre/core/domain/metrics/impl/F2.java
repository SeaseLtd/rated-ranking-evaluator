package io.sease.rre.core.domain.metrics.impl;

/**
 * A F-measure which weighs recall higher than precision (by placing more emphasis on false negatives).
 *
 * @author agazzarini
 * @since 1.0
 */
public class F2 extends FMeasure {
    /**
     * Builds a new F1 metric instance.
     */
    public F2() {
        super("F2", 2);
    }
}
