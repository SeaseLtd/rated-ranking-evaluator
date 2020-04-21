package io.sease.rre.persistence.impl.connector;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.persistence.impl.QueryVersionReport;
import org.apache.http.HttpStatus;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpHead;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.util.EntityUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.elasticsearch.ElasticsearchException;
import org.elasticsearch.action.bulk.BulkProcessor;
import org.elasticsearch.action.bulk.BulkRequest;
import org.elasticsearch.action.bulk.BulkResponse;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.client.Request;
import org.elasticsearch.client.RequestOptions;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.common.xcontent.XContentType;

import java.io.IOException;
import java.util.Collection;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Implementation of {@link ElasticsearchConnector} that includes type mappings
 * in create and index calls.
 * <p>
 * Uses lower-level calls in some places, to keep maximum compatibility with
 * earlier (6.x) versions of Elasticsearch.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class MappingTypeElasticsearchConnector implements ElasticsearchConnector {

    private static final Logger LOGGER = LogManager.getLogger(MappingTypeElasticsearchConnector.class);

    // For ES 6.x and earlier, mapping type must *not* be set to _doc,
    // otherwise it is omitted from requests.
    private static final String DOC_MAPPING_TYPE = "doc";
    static final String MAPPINGS_FILE = "/es6_config.json";

    private final RestHighLevelClient client;

    MappingTypeElasticsearchConnector(RestHighLevelClient client) {
        this.client = client;
    }

    @Override
    public boolean isAvailable() {
        boolean ret = false;

        try {
            final Response response = client.getLowLevelClient().performRequest(new Request(HttpGet.METHOD_NAME, CLUSTER_HEALTH_ENDPOINT));
            final String body = EntityUtils.toString(response.getEntity());
            final Map jsonMap = new ObjectMapper().readValue(body, Map.class);
            if (jsonMap.containsKey("status")) {
                final String status = jsonMap.get("status").toString();
                if ("yellow".equals(status) || "green".equals(status)) {
                    ret = true;
                } else {
                    LOGGER.warn("Cluster status not healthy: {}", status);
                }
            } else {
                LOGGER.warn("No status in _cluster/health response - {}", body);
            }
        } catch (ResponseException e) {
            LOGGER.warn("Caught ResponseException calling {}: {}", CLUSTER_HEALTH_ENDPOINT, e.getResponse().getStatusLine());
        } catch (IOException e) {
            LOGGER.error("Caught IOException calling _cluster/health: {}", e.getMessage());
        }

        return ret;
    }

    @Override
    public boolean indexExists(String index) throws IOException {
        // Use low-level client to avoid ES adding unparseable request
        // parameters that break earlier versions.
        Response response = client.getLowLevelClient().performRequest(new Request(HttpHead.METHOD_NAME, "/" + index));
        return response.getStatusLine().getStatusCode() == HttpStatus.SC_OK;
    }

    @Override
    public boolean createIndex(String index) throws IOException {
        final boolean ret;

        final String configJson = ConnectorUtils.readConfig(
                ConnectorUtils.getStreamForMappingsFile(MAPPINGS_FILE)
                        .orElseThrow(() -> new IOException("Configuration file " + ConnectorUtils.MAPPINGS_FILE + " not available!")));
        try {
            // Use low-level client to avoid ES adding unparseable request
            // parameters that break earlier versions.
            final Request createRequest = new Request(HttpPut.METHOD_NAME, "/" + index);
            createRequest.setJsonEntity(configJson);
            Response response = client.getLowLevelClient().performRequest(createRequest);
            final Map jsonMap = new ObjectMapper().readValue(EntityUtils.toString(response.getEntity()), Map.class);
            if (jsonMap.containsKey("acknowledged")) {
                ret = Boolean.valueOf(jsonMap.get("acknowledged").toString());
            } else {
                ret = false;
            }
        } catch (ElasticsearchException e) {
            LOGGER.warn("Caught ResponseException creating index {}: {}", index, e.getDetailedMessage());
            throw new IOException(e);
        } catch (ResponseException e) {
            LOGGER.warn("Caught ResponseException creating index {}: {}", index, e.getResponse().getStatusLine());
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
                        .type(DOC_MAPPING_TYPE)
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
