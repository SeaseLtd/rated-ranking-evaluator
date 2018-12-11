package io.sease.rre.persistence.impl;

import io.sease.rre.persistence.PersistenceException;
import org.junit.Before;
import org.junit.Test;

import java.io.IOException;
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

    private static final String INDEX = "rre_index";

    private final ElasticsearchConnector elasticsearch = mock(ElasticsearchConnector.class);

    private ElasticsearchPersistenceHandler handler;

    @Before
    public void setupHandler() {
        this.handler = new ElasticsearchPersistenceHandler();
        handler.setElasticsearch(elasticsearch);

        Map<String, Object> config = new HashMap<>();
        config.put(ElasticsearchPersistenceHandler.BASE_URL_KEY, "http://elastic1:9200");
        config.put(ElasticsearchPersistenceHandler.INDEX_KEY, INDEX);
        handler.configure("name", config);
    }

    @Test(expected = PersistenceException.class)
    public void startThrowsException_whenSearchEngineNotAvailable() throws Exception {
        when(elasticsearch.isAvailable()).thenReturn(false);
        handler.beforeStart();
        handler.start();
    }

    @Test(expected = PersistenceException.class)
    public void startThrowsException_whenSearchEngineCannotCheckIndex() throws Exception {
        when(elasticsearch.isAvailable()).thenReturn(true);
        when(elasticsearch.indexExists(INDEX)).thenThrow(new IOException("Error"));

        handler.beforeStart();
        handler.start();
    }

    @Test(expected = PersistenceException.class)
    public void startThrowsException_whenSearchEngineThrowsExceptionOnCreateIndex() throws Exception {
        when(elasticsearch.isAvailable()).thenReturn(true);
        when(elasticsearch.indexExists(INDEX)).thenReturn(false);
        when(elasticsearch.createIndex(INDEX)).thenThrow(new IOException("Error"));

        handler.beforeStart();
        handler.start();
    }

    @Test(expected = PersistenceException.class)
    public void startThrowsException_whenSearchEngineCannotCreateIndex() throws Exception {
        when(elasticsearch.isAvailable()).thenReturn(true);
        when(elasticsearch.indexExists(INDEX)).thenReturn(false);
        when(elasticsearch.createIndex(INDEX)).thenReturn(false);

        handler.beforeStart();
        handler.start();
    }

    @Test
    public void startBehaves_whenSearchEngineAndIndexAvailable() throws Exception {
        when(elasticsearch.isAvailable()).thenReturn(true);
        when(elasticsearch.indexExists(INDEX)).thenReturn(true);
        handler.beforeStart();
        handler.setElasticsearch(elasticsearch);
        handler.start();

        verify(elasticsearch).isAvailable();
    }

    @Test(expected = PersistenceException.class)
    public void startThrowsException_whenIndexCanBeCreated() throws Exception {
        when(elasticsearch.isAvailable()).thenReturn(true);
        when(elasticsearch.indexExists(INDEX)).thenReturn(false);
        when(elasticsearch.createIndex(INDEX)).thenReturn(true);

        handler.beforeStart();
        handler.start();

        verify(elasticsearch).isAvailable();
        verify(elasticsearch).indexExists(INDEX);
        verify(elasticsearch).createIndex(INDEX);
    }
}
