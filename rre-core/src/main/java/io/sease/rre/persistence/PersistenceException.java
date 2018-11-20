package io.sease.rre.persistence;

/**
 * Exception thrown by the persistence framework.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class PersistenceException extends Exception {

    public PersistenceException() {
        super();
    }

    public PersistenceException(String message) {
        super(message);
    }

    public PersistenceException(String message, Throwable cause) {
        super(message, cause);
    }

    public PersistenceException(Throwable cause) {
        super(cause);
    }
}
