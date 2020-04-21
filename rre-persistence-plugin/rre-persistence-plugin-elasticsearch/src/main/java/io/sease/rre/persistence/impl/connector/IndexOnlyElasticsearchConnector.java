package io.sease.rre.persistence.impl.connector;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.persistence.impl.QueryVersionReport;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.ElasticsearchException;
import org.elasticsearch.action.admin.cluster.health.ClusterHealthRequest;
import org.elasticsearch.action.admin.cluster.health.ClusterHealthResponse;
import org.elasticsearch.action.bulk.BulkProcessor;
import org.elasticsearch.action.bulk.BulkRequest;
import org.elasticsearch.action.bulk.BulkResponse;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.client.RequestOptions;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.client.indices.CreateIndexRequest;
import org.elasticsearch.client.indices.GetIndexRequest;
import org.elasticsearch.cluster.health.ClusterHealthStatus;
import org.elasticsearch.common.xcontent.XContentType;

import java.io.IOException;
import java.util.Collection;
import java.util.concurrent.TimeUnit;

/**
 * Implementation of {@link ElasticsearchConnector} that uses the index-only
 * calls required by Elasticsearch 7 and later.
 * <p>
 * Makes use of the higher-level client methods where possible.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class IndexOnlyElasticsearchConnector implements ElasticsearchConnector {

    private static final Logger LOGGER = LogManager.getLogger(IndexOnlyElasticsearchConnector.class);

    static final String MAPPINGS_FILE = "/es7_config.json";

    private final RestHighLevelClient client;

    IndexOnlyElasticsearchConnector(RestHighLevelClient client) {
        this.client = client;
    }

    @Override
    public boolean isAvailable() {
        boolean ret = false;

        try {
            ClusterHealthResponse response = client.cluster().health(new ClusterHealthRequest(), RequestOptions.DEFAULT);
            ClusterHealthStatus status = response.getStatus();
            ret = status.equals(ClusterHealthStatus.GREEN) || status.equals(ClusterHealthStatus.YELLOW);
        } catch (ResponseException e) {
            LOGGER.warn("Caught ResponseException calling {}: {}", CLUSTER_HEALTH_ENDPOINT, e.getResponse().getStatusLine());
        } catch (IOException e) {
            LOGGER.error("Caught IOException calling _cluster/health: {}", e.getMessage());
        }

        return ret;
    }

    @Override
    public boolean indexExists(String index) throws IOException {
        return client.indices().exists(new GetIndexRequest(index), RequestOptions.DEFAULT);
    }

    @Override
    public boolean createIndex(String index) throws IOException {
        final boolean ret;

        final String configJson = ConnectorUtils.readConfig(
                ConnectorUtils.getStreamForMappingsFile(MAPPINGS_FILE)
                        .orElseThrow(() -> new IOException("Configuration file " + MAPPINGS_FILE + " not available!")));
        // Build the request
        CreateIndexRequest request = new CreateIndexRequest(index)
                .source(configJson, XContentType.JSON);

        try {
            ret = client.indices().create(request, RequestOptions.DEFAULT).isAcknowledged();
        } catch (ElasticsearchException e) {
            LOGGER.error("Caught ElasticsearchException creating index {} :: {}", index, e.getDetailedMessage());
            throw new IOException(e);
        }

        return ret;
    }

    @Override
    public void storeItems(String index, Collection<QueryVersionReport> reports) {
        BulkProcessor.Listener listener = new BulkProcessor.Listener() {
            @Override
            public void beforeBulk(long l, BulkRequest bulkRequest) {
                LOGGER.debug("About to execute bulk request of {} actions", bulkRequest.numberOfActions());
            }

            @Override
            public void afterBulk(long l, BulkRequest bulkRequest, BulkResponse bulkResponse) {
                if (bulkResponse.hasFailures()) {
                    LOGGER.warn("Bulk update request had failures!");
                    LOGGER.warn(bulkResponse.buildFailureMessage());
                }
            }

            @Override
            public void afterBulk(long l, BulkRequest bulkRequest, Throwable throwable) {
                LOGGER.error("Caught exception while executing bulk request: " + throwable.getMessage());
            }
        };

        BulkProcessor processor = BulkProcessor.builder((bulkRequest, bulkListener) ->
                client.bulkAsync(bulkRequest, RequestOptions.DEFAULT, bulkListener), listener)
                .build();

        final ObjectMapper mapper = new ObjectMapper();
        reports.forEach(r -> processor.add(
                new IndexRequest(index)
                        .id(r.getId())
                        .source(ConnectorUtils.convertReportToJson(mapper, r), XContentType.JSON)));

        processor.flush();
        try {
            if (!processor.awaitClose(30, TimeUnit.SECONDS)) {
                LOGGER.warn("Bulk update processor was terminated before it could complete operations!");
            }
        } catch (InterruptedException e) {
            LOGGER.error("Bulk update processor was interrupted before it could be closed :: {}", e.getMessage());
        }
    }

    @Override
    public void close() throws IOException {
        client.close();
    }
}
