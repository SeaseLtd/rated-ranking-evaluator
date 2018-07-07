package io.sease.rre.search.api.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import io.sease.rre.search.api.UnableToLoadDataException;
import org.elasticsearch.action.admin.indices.create.CreateIndexRequest;
import org.elasticsearch.action.bulk.BulkRequest;
import org.elasticsearch.action.bulk.BulkResponse;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.action.support.WriteRequest;
import org.elasticsearch.analysis.common.CommonAnalysisPlugin;
import org.elasticsearch.client.Client;
import org.elasticsearch.common.settings.Settings;
import org.elasticsearch.common.xcontent.XContentType;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.node.Node;
import org.elasticsearch.plugins.Plugin;
import org.elasticsearch.search.builder.SearchSourceBuilder;
import org.elasticsearch.transport.Netty4Plugin;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static java.util.Arrays.asList;
import static java.util.Arrays.stream;
import static java.util.stream.Collectors.toList;
import static org.elasticsearch.client.Requests.*;
import static org.elasticsearch.node.InternalSettingsPreparer.prepareEnvironment;

/**
 * Elasticsearch platform API implementation.
 *
 * @author agazzarini
 * @since 1.0
 */
public class Elasticsearch implements SearchPlatform {
    private static class RRENode extends Node {
        RRENode(final Settings settings, final Collection<Class<? extends Plugin>> plugins) {
            super(prepareEnvironment(settings, null), plugins);
        }
    }

    private Client proxy;
    private Node elasticsearch;
    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void beforeStart(final Map<String, Object> configuration) {
        final File logsFolder = new File("target/elasticsearch/logs");
        final File dataFolder = new File("target/elasticsearch/data");

        logsFolder.delete();
        dataFolder.delete();

        logsFolder.mkdirs();
        dataFolder.mkdirs();

        final Settings.Builder settings = Settings.builder()
                .put("path.home", (String) configuration.get("path.home"))
                .put("transport.type", "netty4")
                .put("http.type", "netty4")
                .put("network.host", "127.0.0.1")
                .put("http.port", (Integer) configuration.getOrDefault("network.host", 9200))
                .put("http.enabled", "true")
                .put("path.logs", logsFolder.getAbsolutePath())
                .put("path.data", dataFolder.getAbsolutePath());
        elasticsearch = new RRENode(settings.build(), asList(Netty4Plugin.class, CommonAnalysisPlugin.class));
    }

    @Override
    public void load(final File data, File indexShapeFile, String indexName) {
        if (!indexShapeFile.getName().startsWith("index")) {
            throw new IllegalArgumentException("Unable to find an index-shape (i.e. settings + mappings) within the configuration folder.");
        }

        try {
            final ObjectMapper mapper = new ObjectMapper();
            final JsonNode esconfig = mapper.readTree(indexShapeFile);

            if (proxy.admin().indices().exists(indicesExistsRequest(indexName)).actionGet().isExists()) {
                proxy.admin().indices().delete(deleteIndexRequest(indexName)).actionGet();
            }

            final CreateIndexRequest request = createIndexRequest(indexName)
                    .settings(Settings.builder().loadFromSource(mapper.writeValueAsString(esconfig.get("settings")), XContentType.JSON).build())
                    .mapping("doc", mapper.writeValueAsString(esconfig.get("mappings")), XContentType.JSON);

            proxy.admin().indices().create(request).actionGet();

            final BulkRequest bulkRequest = new BulkRequest();
            final List<String> lines = Files.readAllLines(data.toPath());

            for (int i = 0; i < lines.size(); i += 2) {
                JsonNode metadata = mapper.readTree(lines.get(i)).get("index");
                String document = lines.get(i + 1);
                bulkRequest.add(
                        new IndexRequest(indexName)
                                .type(metadata.get("_type").asText())
                                .id(metadata.get("_id").asText())
                                .source(document, XContentType.JSON)).setRefreshPolicy(WriteRequest.RefreshPolicy.IMMEDIATE);
            }

            final BulkResponse response = proxy.bulk(bulkRequest).actionGet();
            if (response.hasFailures()) {
                final String message =
                        "Unable to load datafile (" +
                                data.getAbsolutePath() +
                                ") in " +
                                getName() +
                                " using the index shape (" +
                                indexShapeFile.getAbsolutePath() +
                                ") into the index " +
                                indexName +
                                ". Error message is: " +
                                response.buildFailureMessage();
                throw new UnableToLoadDataException(message);
            }
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    @Override
    public String getName() {
        return "Elasticsearch";
    }

    @Override
    public void start() {
        try {
            elasticsearch.start();
            proxy = elasticsearch.client();
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }

    @Override
    public void afterStart() {
        // Nothing to be done here
    }

    @Override
    public void beforeStop() {
        // TODO: remove everything
    }

    @Override
    public void close() {
        try {
            elasticsearch.close();
            proxy.close();
        } catch (final IOException ignore) {
            // Ignore
        }
    }

    @Override
    public QueryOrSearchResponse executeQuery(final String indexName, final String query, final String[] fields, final int maxRows) {
        try {
            final String q = mapper.writeValueAsString(mapper.readTree(query).get("query"));
            final SearchSourceBuilder qBuilder = new SearchSourceBuilder().query(QueryBuilders.wrapperQuery(q)).size(maxRows).fetchSource(fields, null);
            final SearchResponse qresponse = proxy.search(new SearchRequest(indexName).source(qBuilder)).actionGet();
            return new QueryOrSearchResponse(
                    qresponse.getHits().totalHits,
                    stream(qresponse.getHits().getHits())
                            .map(hit -> {
                                final Map<String, Object> result = new HashMap(hit.getSourceAsMap());
                                result.put("_id", hit.getId());
                                return result;
                            })
                            .collect(toList()));
        } catch (final IOException exception) {
            throw new RuntimeException(exception);
        }
    }
}
