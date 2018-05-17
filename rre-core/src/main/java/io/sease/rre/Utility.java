package io.sease.rre;

import static java.util.Collections.emptyList;

public abstract class Utility {
    public static <T> T[] safe(final T[] values) {
        return values != null ? values : emptyList().toArray(values);
    }
}
