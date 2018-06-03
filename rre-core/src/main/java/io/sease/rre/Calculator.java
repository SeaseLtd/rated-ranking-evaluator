package io.sease.rre;

import java.math.BigDecimal;
import java.math.RoundingMode;

import static java.util.Arrays.stream;

/**
 * RRE Calculator.
 * Provides a central point for doing math operations.
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

    /**
     * Returns the product of a numbers set.
     *
     * @param numbers the numbers that will be added together.
     * @return the product of all input numbers.
     */
    public static BigDecimal multiply(final BigDecimal ... numbers) {
        return stream(numbers).reduce(BigDecimal.ONE, BigDecimal::multiply);
    }

    /**
     * Executes a subtraction between the two numbers.
     *
     * @param minuend the minuend.
     * @param subtraend the subtraend.
     * @return the result of the subtraction.
     */
    public static BigDecimal subtract(final BigDecimal minuend, final BigDecimal subtraend) {
        return minuend.subtract(subtraend);
    }

    /**
     * Executes a division between the two numbers.
     *
     * @param dividend the dividend.
     * @param divisor the divisor.
     * @return the result of the division.
     */
    public static BigDecimal divide(final BigDecimal dividend, final BigDecimal divisor) {
        return dividend.divide(divisor, 4, RoundingMode.CEILING);
    }

    /**
     * Executes a division between the two numbers.
     *
     * @param dividend the dividend.
     * @param divisor the divisor.
     * @return the result of the division.
     */
    public static BigDecimal divide(final BigDecimal dividend, final int divisor) {
        return dividend.divide(new BigDecimal(divisor), 4, RoundingMode.CEILING);
    }

    /**
     * Executes a division between the two numbers.
     *
     * @param dividend the dividend.
     * @param divisor the divisor.
     * @return the result of the division.
     */
    public static BigDecimal divide(final BigDecimal dividend, final long divisor) {
        return dividend.divide(new BigDecimal(divisor), 4, RoundingMode.CEILING);
    }
}
