package io.sease.rre.persistence;

import io.sease.rre.core.domain.Query;

import java.util.Map;

/**
 * A persistence handler can be used to record the output from all queries
 * run during an evaluation.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public interface PersistenceHandler {

    /**
     * Configure the persistence handler implementation.
     *
     * @param name          the name given to the handler in the main configuration.
     * @param configuration the configuration parameters specific to the
     *                      handler.
     */
    void configure(String name, Map<String, Object> configuration);

    /**
     * Execute any necessary tasks required to initialise the handler.
     */
    void beforeStart();

    /**
     * Execute any necessary start-up tasks.
     */
    void start();

    /**
     * Record a query.
     * @param q the query.
     */
    void recordQuery(Query q);

    /**
     * Execute any tasks necessary before stopping - for example, writing out
     * buffered content.
     */
    void beforeStop();

    /**
     * Execute any necessary shutdown tasks - for example, closing output
     * streams.
     */
    void stop();
}
