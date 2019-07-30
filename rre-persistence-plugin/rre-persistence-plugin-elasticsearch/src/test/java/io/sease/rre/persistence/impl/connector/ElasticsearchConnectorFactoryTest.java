package io.sease.rre.persistence.impl.connector;

import com.google.common.net.MediaType;
import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.mockserver.client.MockServerClient;
import org.mockserver.junit.MockServerRule;
import org.mockserver.model.HttpError;
import org.mockserver.model.HttpRequest;
import org.mockserver.model.HttpResponse;

import java.io.IOException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;

/**
 * Unit tests for the ElasticsearchConnector factory.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class ElasticsearchConnectorFactoryTest {

    @Rule
    public MockServerRule mockServerRule = new MockServerRule(this);

    private MockServerClient mockServerClient;

    private RestHighLevelClient client = mock(RestHighLevelClient.class);
    private ElasticsearchConnectorFactory factory = new ElasticsearchConnectorFactory(client);

    @Before
    public void setupSearchEngine() {
        RestHighLevelClient client = new RestHighLevelClient(
                RestClient.builder(
                        HttpHost.create("http://localhost:" + mockServerRule.getPort())));
        factory = new ElasticsearchConnectorFactory(client);
    }

    @Test(expected = IOException.class)
    public void buildThrowsException_whenServerFails() throws Exception {
        mockServerClient.when(HttpRequest.request().withPath("/"))
                .error(HttpError.error().withDropConnection(true));

        factory.buildConnector();
    }

    @Test(expected = IOException.class)
    public void buildThrowsException_whenBadResponse() throws Exception {
        mockServerClient.when(HttpRequest.request().withPath("/"))
                .respond(HttpResponse.response().withStatusCode(500).withReasonPhrase("Error"));

        factory.buildConnector();
    }

    @Test(expected = IOException.class)
    public void buildThrowsException_forElasticsearch5() throws Exception {
        mockServerClient.when(HttpRequest.request().withPath("/"))
                .respond(HttpResponse.response().withBody("{" +
                        "  \"name\" : \"WrNJ2o6\"," +
                        "  \"cluster_name\" : \"elasticsearch\"," +
                        "  \"cluster_uuid\" : \"QqNMqGgzRsmZDyjZAfel5g\"," +
                        "  \"version\" : {" +
                        "    \"number\" : \"5.6.9\"," +
                        "    \"build_hash\" : \"877a590\"," +
                        "    \"build_date\" : \"2018-04-12T16:25:14.838Z\"," +
                        "    \"build_snapshot\" : false," +
                        "    \"lucene_version\" : \"6.6.1\"" +
                        "  }," +
                        "  \"tagline\" : \"You Know, for Search\"" +
                        "}", MediaType.JSON_UTF_8));

        factory.buildConnector();
    }

    @Test
    public void buildReturnsMappingsConnector_forElasticsearch6() throws Exception {
        mockServerClient.when(HttpRequest.request().withPath("/"))
                .respond(HttpResponse.response().withBody("{" +
                        "  \"name\" : \"jV1j7Sd\"," +
                        "  \"cluster_name\" : \"elasticsearch\"," +
                        "  \"cluster_uuid\" : \"fKmeADu0Rh2I8DVeaCnAVQ\"," +
                        "  \"version\" : {" +
                        "    \"number\" : \"6.2.3\"," +
                        "    \"build_hash\" : \"c59ff00\"," +
                        "    \"build_date\" : \"2018-03-13T10:06:29.741383Z\"," +
                        "    \"build_snapshot\" : false," +
                        "    \"lucene_version\" : \"7.2.1\"," +
                        "    \"minimum_wire_compatibility_version\" : \"5.6.0\"," +
                        "    \"minimum_index_compatibility_version\" : \"5.0.0\"" +
                        "  }," +
                        "  \"tagline\" : \"You Know, for Search\"" +
                        "}", MediaType.JSON_UTF_8));

        ElasticsearchConnector connector = factory.buildConnector();

        assertThat(connector).isInstanceOf(MappingTypeElasticsearchConnector.class);
    }

    @Test
    public void buildReturnsIndexOnlyConnector_forElasticsearch7() throws Exception {
        mockServerClient.when(HttpRequest.request().withPath("/"))
                .respond(HttpResponse.response().withBody("{" +
                        "  \"name\" : \"marla\"," +
                        "  \"cluster_name\" : \"elasticsearch\"," +
                        "  \"cluster_uuid\" : \"nWtbevzBTjOOHnbCmeTSjw\"," +
                        "  \"version\" : {" +
                        "    \"number\" : \"7.2.0\"," +
                        "    \"build_flavor\" : \"default\"," +
                        "    \"build_type\" : \"tar\"," +
                        "    \"build_hash\" : \"508c38a\"," +
                        "    \"build_date\" : \"2019-06-20T15:54:18.811730Z\"," +
                        "    \"build_snapshot\" : false," +
                        "    \"lucene_version\" : \"8.0.0\"," +
                        "    \"minimum_wire_compatibility_version\" : \"6.8.0\"," +
                        "    \"minimum_index_compatibility_version\" : \"6.0.0-beta1\"" +
                        "  }," +
                        "  \"tagline\" : \"You Know, for Search\"" +
                        "}", MediaType.JSON_UTF_8));

        ElasticsearchConnector connector = factory.buildConnector();

        assertThat(connector).isInstanceOf(IndexOnlyElasticsearchConnector.class);
    }
}
