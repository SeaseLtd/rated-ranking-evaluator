package io.sease.rre.persistence.impl.connector;

import io.sease.rre.persistence.impl.QueryVersionReport;

import java.io.IOException;
import java.util.Collection;

/**
 * An Elasticsearch connector provides the functions required to write query
 * reports to an Elasticsearch index.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public interface ElasticsearchConnector {

    String CLUSTER_HEALTH_ENDPOINT = "/_cluster/health";

    /**
     * Is the Elasticsearch cluster available (and healthy)?
     * <p>
     * If this is not true, we won't be able to write anything to
     * Elasticsearch, so the persistence handler should fail.
     *
     * @return {@code true} if the Elasticsearch cluster is available and
     * healthy (ie. the cluster health status is green or yellow).
     */
    boolean isAvailable();

    /**
     * Check whether or not an index exists.
     *
     * @param index the name of the index to check.
     * @return {@code true} if the index exists.
     * @throws IOException if a problem occurs calling the server.
     */
    boolean indexExists(String index) throws IOException;

    /**
     * Create an index, using the mappings read from the mappings file.
     *
     * @param index the name of the index to create.
     * @return {@code true} if the index was successfully created.
     * @throws IOException if there are problems reading the mappings, or
     *                     making the index creation request.
     */
    boolean createIndex(String index) throws IOException;

    /**
     * Store a collection of items to an Elasticsearch index.
     *
     * @param index   the index the items should be written to.
     * @param reports the items to store.
     */
    void storeItems(String index, Collection<QueryVersionReport> reports);

    /**
     * Close the Elasticsearch connector.
     *
     * @throws IOException if problems occur closing the connection.
     */
    void close() throws IOException;
}