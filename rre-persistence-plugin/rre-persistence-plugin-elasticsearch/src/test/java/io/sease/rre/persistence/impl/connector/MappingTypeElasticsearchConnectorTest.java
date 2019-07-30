package io.sease.rre.persistence.impl.connector;

import com.google.common.net.MediaType;
import io.sease.rre.persistence.impl.QueryVersionReport;
import org.apache.http.HttpHost;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpPut;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.mockserver.client.MockServerClient;
import org.mockserver.junit.MockServerRule;
import org.mockserver.model.HttpError;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockserver.model.HttpRequest.request;
import static org.mockserver.model.HttpResponse.response;

/**
 * Unit tests for the MappingType ES Connector implementation.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class MappingTypeElasticsearchConnectorTest {

    private static final String INDEX_NAME = "rre";

    private ElasticsearchConnector connector;

    @Rule
    public MockServerRule mockServerRule = new MockServerRule(this);

    private MockServerClient mockServerClient;

    @Before
    public void setupSearchEngine() {
        RestHighLevelClient client = new RestHighLevelClient(
                RestClient.builder(
                        HttpHost.create("http://localhost:" + mockServerRule.getPort())));
        connector = new MappingTypeElasticsearchConnector(client);
    }


    @Test
    public void isAvailableReturnsFalse_whenStatusIsBad() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(500).withReasonPhrase("Server error"));
        assertThat(connector.isAvailable()).isFalse();
    }

    @Test
    public void isAvailableReturnsFalse_whenNoStatusInBody() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(200).withBody("{}", MediaType.JSON_UTF_8));
        assertThat(connector.isAvailable()).isFalse();
    }

    @Test
    public void isAvailableReturnsFalse_whenStatusRed() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(200).withBody("{ \"status\": \"red\" }", MediaType.JSON_UTF_8));
        assertThat(connector.isAvailable()).isFalse();
    }

    @Test
    public void isAvailableReturnsTrue_whenStatusYellow() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(200).withBody("{ \"status\": \"yellow\" }", MediaType.JSON_UTF_8));
        assertThat(connector.isAvailable()).isTrue();
    }

    @Test
    public void isAvailableReturnsTrue_whenStatusGreen() {
        mockServerClient.when(request().withPath(ElasticsearchConnector.CLUSTER_HEALTH_ENDPOINT))
                .respond(response().withStatusCode(200).withBody("{ \"status\": \"green\" }", MediaType.JSON_UTF_8));
        assertThat(connector.isAvailable()).isTrue();
    }


    @Test(expected = IOException.class)
    public void indexExistsThrowsException_forServerFailure() throws Exception {
        mockServerClient.when(request().withPath("/" + INDEX_NAME))
                .error(HttpError.error().withDropConnection(true));
        connector.indexExists(INDEX_NAME);
    }

    @Test
    public void indexExistsReturnsFalse_whenIndexNotAvailable() throws Exception {
        mockServerClient.when(request().withPath("/" + INDEX_NAME))
                .respond(response().withStatusCode(404));
        assertThat(connector.indexExists(INDEX_NAME)).isFalse();
    }

    @Test
    public void indexExistsReturnsTrue_whenIndexAvailable() throws Exception {
        mockServerClient.when(request().withPath("/" + INDEX_NAME))
                .respond(response().withStatusCode(200));
        assertThat(connector.indexExists(INDEX_NAME)).isTrue();
    }


    @Test(expected = IOException.class)
    public void createIndexThrowsException_forServerFailure() throws Exception {
        mockServerClient.when(request().withPath("/" + INDEX_NAME))
                .error(HttpError.error().withDropConnection(true));
        connector.createIndex(INDEX_NAME);
    }

    @Test(expected = IOException.class)
    public void createIndexThrowsException_whenBadResponse() throws Exception {
        mockServerClient.when(request().withPath("/" + INDEX_NAME))
                .respond(response().withStatusCode(500));
        connector.createIndex(INDEX_NAME);
    }

    @Test
    public void createIndexReturnsFalse_whenCreationFails() throws Exception {
        final String requestBody = ConnectorUtils.readConfig(ConnectorUtils.getStreamForMappingsFile(MappingTypeElasticsearchConnector.MAPPINGS_FILE).get());

        mockServerClient.when(request().withPath("/" + INDEX_NAME).withMethod(HttpPut.METHOD_NAME))
                .respond(response().withBody("{\"error\":" +
                        "{\"root_cause\":" +
                        "[{\"type\":\"resource_already_exists_exception\"," +
                        "\"reason\":\"index [rre/gLXTrMZMQ5S4mav9gdTXtA] already exists\"," +
                        "\"index_uuid\":\"gLXTrMZMQ5S4mav9gdTXtA\"," +
                        "\"index\":\"rre\"}]," +
                        "\"type\":\"resource_already_exists_exception\"," +
                        "\"reason\":\"index [rre/gLXTrMZMQ5S4mav9gdTXtA] already exists\"," +
                        "\"index_uuid\":\"gLXTrMZMQ5S4mav9gdTXtA\"," +
                        "\"index\":\"rre\"}," +
                        "\"status\":400}"));
        assertThat(connector.createIndex(INDEX_NAME)).isFalse();

        mockServerClient.verify(
                request()
                        .withMethod(HttpPut.METHOD_NAME)
                        .withPath("/" + INDEX_NAME)
                        .withBody(requestBody));
    }

    @Test
    public void createIndexReturnsTrue_whenCreationSucceeds() throws Exception {
        final String requestBody = ConnectorUtils.readConfig(ConnectorUtils.getStreamForMappingsFile(MappingTypeElasticsearchConnector.MAPPINGS_FILE).get());

        mockServerClient.when(request().withPath("/" + INDEX_NAME).withMethod(HttpPut.METHOD_NAME))
                .respond(response().withBody("{\"acknowledged\":true,\"shards_acknowledged\":true,\"index\":\"rre\"}"));
        assertThat(connector.createIndex(INDEX_NAME)).isTrue();

        mockServerClient.verify(
                request()
                        .withMethod(HttpPut.METHOD_NAME)
                        .withPath("/" + INDEX_NAME)
                        .withBody(requestBody));
    }


    @Test
    public void storeItems() {
        final Collection<QueryVersionReport.VersionMetric> emptyMetrics = Collections.emptyList();
        final Collection<QueryVersionReport.Result> emptyResult = Collections.emptyList();
        final QueryVersionReport qvr1 = new QueryVersionReport("1", null, null, null, null, "1.0", 0, emptyMetrics, emptyResult);
        final QueryVersionReport qvr2 = new QueryVersionReport("2", null, null, null, null, "1.1", 0, emptyMetrics, emptyResult);

        mockServerClient.when(request()
                .withPath("/_bulk")
                .withMethod(HttpPost.METHOD_NAME))
                .respond(response()
                        .withBody("{\"took\":63,\"errors\":false,\"items\":" +
                                "[{\"index\":{\"_index\":\"rre\",\"_type\":\"_doc\",\"_id\":\"1\",\"_version\":1,\"result\":\"created\",\"_shards\":{\"total\":2,\"successful\":1,\"failed\":0},\"_seq_no\":0,\"_primary_term\":4,\"status\":201}}," +
                                "{\"index\":{\"_index\":\"rre\",\"_type\":\"_doc\",\"_id\":\"2\",\"_version\":1,\"result\":\"created\",\"_shards\":{\"total\":2,\"successful\":1,\"failed\":0},\"_seq_no\":0,\"_primary_term\":4,\"status\":201}}]}"));

        connector.storeItems(INDEX_NAME, Arrays.asList(qvr1, qvr2));

        mockServerClient.verify(
                request()
                        .withMethod(HttpPost.METHOD_NAME)
                        .withPath("/_bulk")
                        .withBody("{\"index\":{\"_index\":\"rre\",\"_type\":\"doc\",\"_id\":\"1\"}}\n" +
                                "{\"id\":\"1\",\"version\":\"1.0\",\"totalHits\":0}\n" +
                                "{\"index\":{\"_index\":\"rre\",\"_type\":\"doc\",\"_id\":\"2\"}}\n" +
                                "{\"id\":\"2\",\"version\":\"1.1\",\"totalHits\":0}\n"));
    }
}
