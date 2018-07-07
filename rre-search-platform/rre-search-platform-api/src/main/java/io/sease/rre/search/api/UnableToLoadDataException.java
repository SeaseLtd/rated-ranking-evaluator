package io.sease.rre.search.api;

/**
 * Marker exception for indicating a failure in the dataset load phase.
 *
 * @author agazzarini
 * @since 1.0
 */
public class UnableToLoadDataException extends RuntimeException {
    /**
     * Builds a new exception with the given message.
     *
     * @param message the exception message.
     */
    public UnableToLoadDataException(final String message) {
        super(message);
    }

    /**
     * Builds a new exception with the given cause.
     *
     * @param cause the exception cause.
     */
    public UnableToLoadDataException(final Throwable cause) {
        super(cause);
    }

}
