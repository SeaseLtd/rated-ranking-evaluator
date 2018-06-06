package io.sease.rre.server;

import java.math.BigDecimal;

public class Func {
    public boolean isZero(final BigDecimal v) {
        return v != null && v.doubleValue() == 0;
    }

    public boolean isPositive(final BigDecimal v) {
        return v.compareTo(BigDecimal.ZERO) > 0;
    }
}
