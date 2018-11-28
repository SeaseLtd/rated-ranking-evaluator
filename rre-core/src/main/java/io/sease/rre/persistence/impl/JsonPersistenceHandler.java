package io.sease.rre.persistence.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.ObjectWriter;
import io.sease.rre.core.domain.DomainMember;
import io.sease.rre.core.domain.Evaluation;
import io.sease.rre.core.domain.Query;
import io.sease.rre.persistence.PersistenceException;
import io.sease.rre.persistence.PersistenceHandler;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * JSON implementation of the {@link PersistenceHandler} interface.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class JsonPersistenceHandler implements PersistenceHandler {

    static final String DESTINATION_FILE_CONFIGKEY = "destinationFile";
    static final String PRETTY_CONFIGKEY = "pretty";

    public static final String DEFAULT_OUTPUT_FILE = "target/rre/evaluation.json";

    private static final Logger LOGGER = LogManager.getLogger(JsonPersistenceHandler.class);

    private String name;
    private String outputFilepath;
    private boolean pretty;

    private List<Query> queries = new ArrayList<>();

    @Override
    public void configure(String name, Map<String, Object> configuration) {
        this.name = name;
        this.outputFilepath = configuration.getOrDefault(DESTINATION_FILE_CONFIGKEY, DEFAULT_OUTPUT_FILE).toString();
        this.pretty = Boolean.valueOf(configuration.getOrDefault(PRETTY_CONFIGKEY, "false").toString());
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public void beforeStart() throws PersistenceException {
        // Delete the output file if it already exists
        Path outPath = Paths.get(outputFilepath);
        if (Files.exists(outPath)) {
            try {
                Files.delete(outPath);
            } catch (IOException e) {
                throw new PersistenceException("Cannot delete pre-existing output file " + outputFilepath, e);
            }
        } else {
            // Make sure the file's parent directory exists
            if (outPath.getParent() != null) {
                try {
                    Files.createDirectories(outPath.getParent());
                } catch (IOException e) {
                    throw new PersistenceException("Cannot create output directory " + outPath.getParent(), e);
                }
            }
        }

        try (FileOutputStream fos = new FileOutputStream(outPath.toFile())) {
            fos.write(new byte[0]);
        } catch (IOException e) {
            throw new PersistenceException("Cannot write to output file " + outputFilepath, e);
        }
    }

    @Override
    public void start() {
        // Nothing to start
    }

    @Override
    public void recordQuery(Query q) {
        queries.add(q);
    }

    @Override
    public void beforeStop() {
        // Collect the metrics for all of the queries
        queries.forEach(Query::notifyCollectedMetrics);

        // Retrieve the top level item
        DomainMember topLevel = findTopLevel();
        try {
            // Write out the JSON object
            ObjectMapper mapper = new ObjectMapper();
            ObjectWriter writer = (pretty ? mapper.writerWithDefaultPrettyPrinter() : mapper.writer());
            writer.writeValue(new File(outputFilepath), topLevel);
        } catch (IOException e) {
            LOGGER.error("Caught IOException writing queries to JSON :: " + e.getMessage());
        }
    }

    private Optional<DomainMember<?>> retrieveParent(DomainMember<?> dm) {
        if (dm.getParent().isPresent()) {
            return retrieveParent(dm.getParent().get());
        } else {
            return Optional.of(dm);
        }
    }

    private DomainMember findTopLevel() {
        if (queries.size() > 0) {
            // Get the first query, then iterate through the parents to the top
            return retrieveParent(queries.get(0)).orElse(new Evaluation());
        } else {
            // No queries - return an empty Evaluation object
            LOGGER.warn("No queries recorded - returning empty evaluation");
            return new Evaluation();
        }
    }

    @Override
    public void stop() {
        // Nothing to stop
    }
}
