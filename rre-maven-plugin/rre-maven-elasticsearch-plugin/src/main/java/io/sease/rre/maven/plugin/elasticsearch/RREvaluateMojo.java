package io.sease.rre.maven.plugin.elasticsearch;

import io.sease.rre.core.Engine;
import io.sease.rre.core.domain.metrics.MetricClassManager;
import io.sease.rre.core.domain.metrics.ParameterizedMetricClassManager;
import io.sease.rre.core.domain.metrics.SimpleMetricClassManager;
import io.sease.rre.persistence.PersistenceConfiguration;
import io.sease.rre.search.api.SearchPlatform;
import io.sease.rre.search.api.impl.Elasticsearch;
import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * RREvalutation Mojo (Apache Solr binding).
 *
 * @author agazzarini
 * @since 1.0
 */
@Mojo(name = "evaluate", inheritByDefault = false, defaultPhase = LifecyclePhase.PACKAGE, threadSafe = true)
public class RREvaluateMojo extends AbstractMojo {

    @Parameter( defaultValue = "${project.compileClasspathElements}", readonly = true, required = true )
    private List<String> compilePaths;

    @Parameter(name = "configurations-folder", defaultValue = "${basedir}/src/etc/configuration_sets")
    private String configurationsFolder;

    @Parameter(name = "corpora-folder", defaultValue = "${basedir}/src/etc/datasets")
    private String corporaFolder;

    @Parameter(name = "ratings-folder", defaultValue = "${basedir}/src/etc/ratings)")
    private String ratingsFolder;

    @Parameter(name = "templates-folder", defaultValue = "${basedir}/src/etc/templates")
    private String templatesFolder;

    @Parameter(name = "data-folder", defaultValue = "target/elasticsearch/data")
    private String dataFolder;

    @Parameter(name = "force-refresh", defaultValue = "true")
    private boolean forceRefresh;

    @Parameter(name = "checksum-file")
    private String checksumFile;

    @Parameter(name = "metrics", defaultValue = "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne,io.sease.rre.core.domain.metrics.impl.PrecisionAtTwo,io.sease.rre.core.domain.metrics.impl.PrecisionAtThree,io.sease.rre.core.domain.metrics.impl.PrecisionAtTen")
    private List<String> metrics;

    @Parameter(name = "parameterizedMetrics")
    private Map<String, Map> parameterizedMetrics;

    @Parameter(name = "plugins")
    private List<String> plugins;

    @Parameter(name = "include")
    private List<String> include;

    @Parameter(name = "exclude")
    private List<String> exclude;

    @Parameter(name = "fields", defaultValue = "")
    private String fields;

    @Parameter(name = "port", defaultValue = "9200")
    private int port;

    @Parameter(name = "persistence")
    private PersistenceConfiguration persistence = PersistenceConfiguration.DEFAULT_CONFIG;

    @Override
    public void execute() throws MojoExecutionException {
        final URL [] urls = compilePaths.stream()
                .map(path -> {
                    try {
                        return new File(path).toURI().toURL();
                    } catch (final Exception exception) {
                        throw new IllegalArgumentException(exception);
                    }})
                .toArray(URL[]::new);

        Thread.currentThread()
                .setContextClassLoader(
                        URLClassLoader.newInstance(
                            urls,
                            Thread.currentThread().getContextClassLoader()));

        try (final SearchPlatform platform = new Elasticsearch()) {
            final MetricClassManager metricClassManager =
                    parameterizedMetrics == null ? new SimpleMetricClassManager(metrics) : new ParameterizedMetricClassManager(metrics, parameterizedMetrics);
            final Engine engine = new Engine(
                    platform,
                    configurationsFolder,
                    corporaFolder,
                    ratingsFolder,
                    templatesFolder,
                    metricClassManager,
                    fields.split(","),
                    exclude,
                    include,
                    checksumFile,
                    persistence);

            final Map<String, Object> configuration = new HashMap<>();
            configuration.put("path.home", "/tmp");
            configuration.put("path.data", dataFolder);
            configuration.put("network.host", port);
            configuration.put("plugins", plugins);
            configuration.put("forceRefresh", forceRefresh);

            engine.evaluate(configuration);
        } catch (final IOException exception) {
            throw new MojoExecutionException(exception.getMessage(), exception);
        }
    }

    // Used by unit test
    PersistenceConfiguration getPersistence() {
        return persistence;
    }
}