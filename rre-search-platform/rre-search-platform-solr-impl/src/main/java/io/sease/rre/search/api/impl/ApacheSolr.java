package io.sease.rre.search.api.impl;

import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import org.apache.htrace.fasterxml.jackson.databind.JsonNode;
import org.apache.htrace.fasterxml.jackson.databind.ObjectMapper;
import org.apache.log4j.LogManager;
import org.apache.log4j.Logger;
import org.apache.solr.client.solrj.SolrQuery;
import org.apache.solr.client.solrj.embedded.EmbeddedSolrServer;
import org.apache.solr.client.solrj.response.UpdateResponse;
import org.apache.solr.common.SolrException;
import org.apache.solr.core.CoreContainer;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.Map;

import static java.util.Collections.emptyMap;
import static java.util.Optional.of;
import static java.util.Optional.ofNullable;

/**
 * Apache Solr search platform API implementation.
 *
 * @author agazzarini
 * @since 1.0
 */
public class ApacheSolr implements SearchPlatform {

    private static final Logger LOGGER = LogManager.getLogger(ApacheSolr.class);

    private EmbeddedSolrServer proxy;
    private File solrHome;
    private File coreProperties;
    private File renamedCoreProperties;

    @Override
    public void beforeStart(final Map<String, Object> configuration) {
        solrHome = new File(
                (String) configuration.getOrDefault("solr.home", "/tmp"),
                String.valueOf(System.currentTimeMillis()));
        prepareSolrHome(solrHome);


        final File parentDataDir = new File((String) configuration.getOrDefault("solr.data.dir", "/tmp"));
        System.setProperty(
                "solr.data.dir",
                new File(parentDataDir, String.valueOf(System.currentTimeMillis())).getAbsolutePath());

        proxy = new EmbeddedSolrServer(solrHome.toPath(), "dummy");
    }

    @Override
    public void load(final File data, final File configFolder, final String targetIndexName) {
        coreProperties = new File(configFolder, "core.properties");
        if (coreProperties.exists()) {
            renamedCoreProperties = new File(configFolder, "core.properties.ignore");
            coreProperties.renameTo(renamedCoreProperties);
        }

        proxy.getCoreContainer().create(targetIndexName, configFolder.toPath(), emptyMap(), true);

        try {
            UpdateResponse response = new JsonUpdateRequest(new FileInputStream(data)).process(proxy, targetIndexName);
            if (response.getStatus() != 0) {
                throw new IllegalArgumentException("Received an error status from Solr: " + response.getStatus());
            }
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    @Override
    public void start() {
        // Nothing to be done here, the embedded server doesn't need an explicit start command.
    }

    @Override
    public void afterStart() {
        // Nothing to be done here.
    }

    @Override
    public void beforeStop() {
        ofNullable(proxy).ifPresent(solr -> {
            try {
                solr.deleteByQuery("*:*");
                solr.commit();
            } catch (final Exception exception) {
                exception.printStackTrace();
            }
        });
    }

    @Override
    public void close() {
        ofNullable(proxy).ifPresent(solr -> {
            try {
                solr.close();
            } catch (final Exception exception) {
                exception.printStackTrace();
            }
        });

        ofNullable(proxy)
                .map(EmbeddedSolrServer::getCoreContainer)
                .map(CoreContainer::getAllCoreNames)
                .orElse(Collections.emptyList())
                .forEach(coreName ->
                            proxy.getCoreContainer().unload(coreName, true, true, false));

        ofNullable(renamedCoreProperties).ifPresent(file -> file.renameTo(coreProperties));

        solrHome.deleteOnExit();
    }

    @Override
    public QueryOrSearchResponse executeQuery(final String coreName, final String queryString, final String[] fields, final int maxRows) {
        try {
            final SolrQuery query =
                    new SolrQuery()
                            .setRows(maxRows)
                            .setFields(fields);
            final ObjectMapper mapper = new ObjectMapper();
            final JsonNode queryDef = mapper.readTree(queryString);

            for (final Iterator<Map.Entry<String, JsonNode>> iterator = queryDef.fields(); iterator.hasNext(); ) {
                final Map.Entry<String, JsonNode> field = iterator.next();
                query.add(field.getKey(), field.getValue().asText());
            }

            return of(proxy.query(coreName, query))
                    .map(response ->
                            new QueryOrSearchResponse(
                                    response.getResults().getNumFound(),
                                    new ArrayList<Map<String, Object>>(response.getResults())))
                    .get();
        }
        catch (SolrException e) {
            LOGGER.error("Caught Solr exception :: " + e.getMessage());
            return new QueryOrSearchResponse(0, Collections.emptyList());
        }
        catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    @Override
    public String getName() {
        return "Apache Solr";
    }

    /**
     * Setup the Solr instance by preparing a minimal solr.home directory.
     *
     * @param folder the folder where the temporary solr.home will be created.
     */
    private void prepareSolrHome(final File folder) {
        folder.mkdirs();
        try (final BufferedWriter writer = new BufferedWriter(new FileWriter(new File(folder, "solr.xml")))) {
            writer.write("<solr/>");

            final File dummyCoreHome = new File(folder, "dummy");
            final File dummyCoreConf = new File(dummyCoreHome, "conf");
            dummyCoreConf.mkdirs();

            Files.copy(getClass().getResourceAsStream("/schema.xml"), new File(dummyCoreConf, "schema.xml").toPath(), StandardCopyOption.REPLACE_EXISTING);
            Files.copy(getClass().getResourceAsStream("/solrconfig.xml"), new File(dummyCoreConf, "solrconfig.xml").toPath(), StandardCopyOption.REPLACE_EXISTING);
            Files.copy(getClass().getResourceAsStream("/core.properties"), new File(dummyCoreHome, "core.properties").toPath(), StandardCopyOption.REPLACE_EXISTING);

        } catch (final Exception exception) {
            folder.deleteOnExit();
            throw new RuntimeException(exception);
        }
    }
}
