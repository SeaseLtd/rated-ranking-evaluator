package io.sease.rre;

import static java.util.Collections.emptyList;

/**
 * Shared utilities.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class Utility {

    /**
     * Makes sure a non-null array is returned.
     * This is used in iterations, in order to avoid NPE.
     *
     * @param values the input array.
     * @param <T> the array type.
     * @return the same array, if it's not null, an empty array otherwise.
     */
    public static <T> T[] safe(final T[] values) {
        return values != null ? values : emptyList().toArray(values);
    }
}
