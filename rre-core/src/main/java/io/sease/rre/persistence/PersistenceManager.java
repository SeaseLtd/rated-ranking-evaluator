package io.sease.rre.persistence;

import io.sease.rre.core.domain.Query;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * The general manager class for all persistence handlers. This provides
 * methods for starting, processing, and shutting down a number of handlers
 * via single method calls.
 * <p>
 * Persistence handlers should be constructed outside the manager, including
 * any required initialisation via the {@link PersistenceHandler#configure(String, Map)}
 * method, then registered using {@link #registerHandler(PersistenceHandler)}.
 * <p>
 * Most other methods apply to all registered handlers.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class PersistenceManager {

    private final List<PersistenceHandler> handlers = new ArrayList<>();

    public void registerHandler(PersistenceHandler handler) {
        handlers.add(handler);
    }

    public void beforeStart() {
        handlers.parallelStream().forEach(PersistenceHandler::beforeStart);
    }

    public void start() {
        handlers.parallelStream().forEach(PersistenceHandler::start);
    }

    public void recordQuery(Query query) {
        handlers.parallelStream().forEach(h -> h.recordQuery(query));
    }

    public void beforeStop() {
        handlers.parallelStream().forEach(PersistenceHandler::beforeStop);
    }

    public void stop() {
        handlers.parallelStream().forEach(PersistenceHandler::stop);
    }
}
