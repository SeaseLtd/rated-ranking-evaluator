package io.sease.rre.persistence.impl.connector;

import io.sease.rre.persistence.impl.QueryVersionReport;
import org.elasticsearch.client.RestHighLevelClient;

import java.io.IOException;
import java.util.Collection;

/**
 * Implementation of {@link ElasticsearchConnector} that uses the index-only
 * calls required by Elasticsearch 7 and later.
 * <p>
 * Makes use of the higher-level client methods where possible.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class IndexOnlyElasticsearchConnector implements ElasticsearchConnector {

    private final RestHighLevelClient client;

    public IndexOnlyElasticsearchConnector(RestHighLevelClient client) {
        this.client = client;
    }

    @Override
    public boolean isAvailable() {
        return false;
    }

    @Override
    public boolean indexExists(String index) throws IOException {
        return false;
    }

    @Override
    public boolean createIndex(String index) throws IOException {
        return false;
    }

    @Override
    public void storeItems(String index, Collection<QueryVersionReport> reports) {

    }

    @Override
    public void close() throws IOException {

    }
}
