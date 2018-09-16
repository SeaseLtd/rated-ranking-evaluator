package io.sease.rre.core.domain.metrics.impl;

/**
 * The most popular F-Measure, which balances between precisin and recall using 1 as beta factor.
 *
 * @author agazzarini
 * @since 1.0
 */
public class F1 extends FMeasure {
    /**
     * Builds a new F1 metric instance.
     */
    public F1() {
        super("F1", 1);
    }
}
