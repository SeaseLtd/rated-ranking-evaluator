package io.sease.rre.persistence.impl;

import io.sease.rre.persistence.PersistenceException;
import org.junit.Before;
import org.junit.Test;

import java.util.HashMap;
import java.util.Map;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Client-specific unit tests for the Elasticsearch Persistence handler.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class ElasticsearchPersistenceHandlerClientTest {

    private final ElasticsearchConnector elasticsearch = mock(ElasticsearchConnector.class);

    private ElasticsearchPersistenceHandler handler;

    @Before
    public void setupHandler() {
        this.handler = new ElasticsearchPersistenceHandler();
        handler.setElasticsearch(elasticsearch);

        Map<String, Object> config = new HashMap<>();
        config.put(ElasticsearchPersistenceHandler.BASE_URL_KEY, "http://elastic1:9200");
        handler.configure("name", config);
    }

    @Test(expected = PersistenceException.class)
    public void startThrowsException_whenSearchEngineNotAvailable() throws Exception {
        when(elasticsearch.isAvailable()).thenReturn(false);
        handler.start();
    }

    @Test
    public void startBehaves_whenSearchEngineAvailable() throws Exception {
        when(elasticsearch.isAvailable()).thenReturn(true);
        handler.start();

        verify(elasticsearch).isAvailable();
    }
}
