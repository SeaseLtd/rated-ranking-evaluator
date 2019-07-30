package io.sease.rre.persistence.impl.connector;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.ElasticsearchException;
import org.elasticsearch.Version;
import org.elasticsearch.client.RequestOptions;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.client.core.MainResponse;

import java.io.IOException;

/**
 * Factory class for building an ElasticsearchConnector implementation,
 * based on the Elasticsearch version in use.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class ElasticsearchConnectorFactory {

    private static final Logger LOGGER = LogManager.getLogger(ElasticsearchConnectorFactory.class);

    private final RestHighLevelClient client;

    public ElasticsearchConnectorFactory(RestHighLevelClient client) {
        this.client = client;
    }

    public ElasticsearchConnector buildConnector() throws IOException {
        final ElasticsearchConnector connector;

        if (versionAllowsTypes(getVersionDetails())) {
            connector = new MappingTypeElasticsearchConnector(client);
        } else {
            connector = new IndexOnlyElasticsearchConnector(client);
        }

        return connector;
    }

    private MainResponse.Version getVersionDetails() throws IOException {
        try {
            return client.info(RequestOptions.DEFAULT).getVersion();
        } catch (ElasticsearchException e) {
            LOGGER.error("Caught ES exception :: {}", e.getMessage());
            throw new IOException(e);
        }
    }

    private boolean versionAllowsTypes(MainResponse.Version version) {
        String versionNumber = version.getNumber();
        int majorVersion = Integer.valueOf(versionNumber.split("\\.")[0]);
        return majorVersion < 7;
    }
}
