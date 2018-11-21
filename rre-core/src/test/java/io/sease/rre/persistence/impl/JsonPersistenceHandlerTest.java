package io.sease.rre.persistence.impl;

import io.sease.rre.persistence.PersistenceException;
import io.sease.rre.persistence.PersistenceHandler;
import org.junit.After;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;
import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/**
 * Unit tests for the JSON PersistenceHandler implementation.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class JsonPersistenceHandlerTest {

    private static final String HANDLER_NAME = "jsonTest";

    @Rule
    public TemporaryFolder folder = new TemporaryFolder();

    private PersistenceHandler handler;

    @Before
    public void setupHandler() {
        this.handler = new JsonPersistenceHandler();
    }

    @After
    public void tearDownHandler() {
        this.handler = null;
    }

    @Test
    public void beforeStartThrowsException_whenFileCannotBeDeleted() throws Exception {
        File outFile = folder.newFile();
        outFile.setReadOnly();

        Map<String, Object> config = new HashMap<>();
        config.put(JsonPersistenceHandler.DESTINATION_FILE_CONFIGKEY, outFile.getAbsolutePath());
        handler.configure(HANDLER_NAME, config);

        try {
            handler.beforeStart();
            fail("Expected PersistenceException");
        } catch (PersistenceException e) {
            // Expected behaviour
        }
    }

    @Test
    public void beforeStartPasses_whenFileExists() throws Exception {
        File outFile = folder.newFile();

        Map<String, Object> config = new HashMap<>();
        config.put(JsonPersistenceHandler.DESTINATION_FILE_CONFIGKEY, outFile.getAbsolutePath());
        handler.configure(HANDLER_NAME, config);

        handler.beforeStart();
    }

    @Test
    public void beforeStartPasses_whenDestinationDirNotExist() throws Exception {
        Map<String, Object> config = new HashMap<>();
        config.put(JsonPersistenceHandler.DESTINATION_FILE_CONFIGKEY, folder.getRoot().getAbsolutePath() + "/target/rre/evaluation.json");
        handler.configure(HANDLER_NAME, config);

        handler.beforeStart();

        File target = new File(folder.getRoot(), "target/rre/evaluation.json");
        assertTrue(target.exists());
        assertTrue(target.canWrite());
    }

    @Test
    public void beforeStop_handlesEmptyQueryList() throws Exception {
        File outFile = folder.newFile();
        Map<String, Object> config = new HashMap<>();
        config.put(JsonPersistenceHandler.DESTINATION_FILE_CONFIGKEY, outFile.getAbsolutePath());
        config.put(JsonPersistenceHandler.PRETTY_CONFIGKEY, true);
        handler.configure(HANDLER_NAME, config);

        handler.beforeStop();

        assertTrue(outFile.exists());
        assertTrue(outFile.length() != 0);
    }
}
