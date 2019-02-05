/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
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
    public static BigDecimal sum(final BigDecimal... addends) {
        return stream(addends).reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    /**
     * Returns the product of a numbers set.
     *
     * @param numbers the numbers that will be added together.
     * @return the product of all input numbers.
     */
    public static BigDecimal multiply(final BigDecimal... numbers) {
        return stream(numbers).reduce(BigDecimal.ONE, BigDecimal::multiply);
    }

    /**
     * Executes a subtraction between the two numbers.
     *
     * @param minuend   the minuend.
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
     * @param divisor  the divisor.
     * @return the result of the division.
     */
    public static BigDecimal divide(final BigDecimal dividend, final BigDecimal divisor) {
        return dividend.divide(divisor, 4, RoundingMode.CEILING);
    }

    /**
     * Executes a division between the two numbers.
     *
     * @param dividend the dividend.
     * @param divisor  the divisor.
     * @return the result of the division.
     */
    public static BigDecimal divide(final BigDecimal dividend, final int divisor) {
        return dividend.divide(new BigDecimal(divisor), 4, RoundingMode.CEILING);
    }

    /**
     * Executes a division between the two numbers.
     *
     * @param dividend the dividend.
     * @param divisor  the divisor.
     * @return the result of the division.
     */
    public static BigDecimal divide(final BigDecimal dividend, final long divisor) {
        return dividend.divide(new BigDecimal(divisor), 4, RoundingMode.CEILING);
    }
}
