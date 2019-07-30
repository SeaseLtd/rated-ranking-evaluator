package io.sease.rre.persistence.impl.connector;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.persistence.impl.QueryVersionReport;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.Optional;

/**
 * Utility methods for {@link ElasticsearchConnector} implementations.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
abstract class ConnectorUtils {

    private static final Logger LOGGER = LogManager.getLogger(ConnectorUtils.class);

    static final String MAPPINGS_FILE = "/es_config.json";

    /**
     * Get the input stream for a file on the local classpath (eg. one held in
     * the resources directory.
     *
     * @param filePath the path for the file.
     * @return an optional input stream for the file, empty if the file does
     * not exist.
     */
    static Optional<InputStream> getStreamForMappingsFile(String filePath) {
        return Optional.ofNullable(ConnectorUtils.class.getResourceAsStream(filePath));
    }

    /**
     * Read the index configuration file stream and return it as a String.
     *
     * @param inputStream the input stream for the configuration file.
     * @return the index configuration file.
     * @throws IOException if the file cannot be read.
     */
    static String readConfig(InputStream inputStream) throws IOException {
        final StringWriter sw = new StringWriter();
        final PrintWriter pw = new PrintWriter(sw);

        try (BufferedReader br = new BufferedReader(new InputStreamReader(inputStream))) {
            String line;
            while ((line = br.readLine()) != null) {
                pw.println(line);
            }
            pw.close();
        } catch (IOException e) {
            LOGGER.error("IOException reading mappings :: {}", e.getMessage());
            throw (e);
        }

        return sw.toString();
    }

    /**
     * Convert a {@link QueryVersionReport} to JSON using an object mapper.
     *
     * @param mapper the ObjectMapper to use to carry out the conversion.
     * @param report the report to be converted.
     * @return a String representing the JSON object.
     */
    static String convertReportToJson(ObjectMapper mapper, QueryVersionReport report) {
        String json = null;

        try {
            json = mapper.writeValueAsString(report);
        } catch (JsonProcessingException e) {
            LOGGER.error("Could not convert versioned query report to JSON for Elasticsearch: {}", e.getMessage());
        }

        return json;
    }

}
