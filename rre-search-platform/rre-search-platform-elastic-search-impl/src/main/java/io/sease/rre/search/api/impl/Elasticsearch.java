package io.sease.rre.search.api.impl;

import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import org.elasticsearch.analysis.common.CommonAnalysisPlugin;
import org.elasticsearch.client.Client;
import org.elasticsearch.common.settings.Settings;
import org.elasticsearch.node.Node;
import org.elasticsearch.plugins.Plugin;
import org.elasticsearch.transport.Netty4Plugin;

import java.io.File;
import java.util.Collection;
import java.util.Map;

import static java.util.Arrays.asList;
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

    @Override
    public void beforeStart(final Map<String, Object> configuration) {
        Settings.Builder settings = Settings.builder()
                .put("path.home", (String)configuration.get("path.home"))
                .put("transport.type", "netty4")
                .put("http.type", "netty4")
                .put("network.host", (Integer)configuration.getOrDefault("network.host", 9200))
                .put("http.enabled", "true")
                .put("path.logs", "target")
                .put("path.data", "target");
        elasticsearch = new RRENode(settings.build(), asList(Netty4Plugin.class, CommonAnalysisPlugin.class));
    }

    @Override
    public void load(File data, File configFolder, String targetIndexName) {

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

    }

    @Override
    public void close() {

    }

    @Override
    public QueryOrSearchResponse executeQuery(String indexName, String query) {
        return null;
    }
}
