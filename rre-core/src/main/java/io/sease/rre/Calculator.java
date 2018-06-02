package io.sease.rre;

import java.math.BigDecimal;
import java.math.RoundingMode;

import static java.util.Arrays.stream;

/**
 * RRE Calculator.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class Calculator {

    /**
     * Executes the sum of the given addends.
     *
     * @param addends the numbers that will be added together.
     * @return the sum of all input addends.
     */
    public static BigDecimal sum(final BigDecimal ... addends) {
        return stream(addends).reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public static BigDecimal multiply(final BigDecimal ... numbers) {
        return stream(numbers).reduce(BigDecimal.ONE, BigDecimal::multiply);
    }

    public static BigDecimal subtract(final BigDecimal minuend, final BigDecimal subtraend) {
        return minuend.subtract(subtraend);
    }

    public static BigDecimal divide(final BigDecimal dividend, final BigDecimal divisor) {
        return dividend.divide(divisor, 4, RoundingMode.CEILING);
    }

    public static BigDecimal divide(final BigDecimal dividend, final int divisor) {
        return dividend.divide(new BigDecimal(divisor), 4, RoundingMode.CEILING);
    }
}
