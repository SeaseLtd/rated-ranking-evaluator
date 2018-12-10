package io.sease.rre.server.services;

/**
 * Exception thrown during evaluation handling.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class EvaluationHandlerException extends Exception {

    public EvaluationHandlerException() {
    }

    public EvaluationHandlerException(String message) {
        super(message);
    }

    public EvaluationHandlerException(String message, Throwable cause) {
        super(message, cause);
    }

    public EvaluationHandlerException(Throwable cause) {
        super(cause);
    }
}
