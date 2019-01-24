package io.sease.rre.maven.plugin.solr;

import io.sease.rre.core.Engine;
import io.sease.rre.core.domain.metrics.SimpleMetricClassManager;
import io.sease.rre.persistence.PersistenceConfiguration;
import io.sease.rre.search.api.SearchPlatform;
import io.sease.rre.search.api.impl.ApacheSolr;
import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * RREvalutation Mojo (Apache Solr binding).
 *
 * @author agazzarini
 * @since 1.0
 */
@Mojo(name = "evaluate", inheritByDefault = false, defaultPhase = LifecyclePhase.PACKAGE)
public class RREvaluateMojo extends AbstractMojo {

    @Parameter(name = "configurations-folder", defaultValue = "${basedir}/src/etc/configuration_sets")
    private String configurationsFolder;

    @Parameter(name = "corpora-folder", defaultValue = "${basedir}/src/etc/corpora")
    private String corporaFolder;

    @Parameter(name = "ratings-folder", defaultValue = "${basedir}/src/etc/ratings)")
    private String ratingsFolder;

    @Parameter(name = "templates-folder", defaultValue = "${basedir}/src/etc/templates")
    private String templatesFolder;

    @Parameter(name = "data-folder")
    private String dataFolder;

    @Parameter(name = "force-refresh", defaultValue = "true")
    private boolean forceRefresh;

    @Parameter(name = "checksum-file")
    private String checksumFile;

    @Parameter(name = "metrics", defaultValue = "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne,io.sease.rre.core.domain.metrics.impl.PrecisionAtTwo,io.sease.rre.core.domain.metrics.impl.PrecisionAtThree,io.sease.rre.core.domain.metrics.impl.PrecisionAtTen")
    private List<String> metrics;

    @Parameter(name = "fields", defaultValue = "*,score")
    private String fields;

    @Parameter(name = "include")
    private List<String> include;

    @Parameter(name = "exclude")
    private List<String> exclude;

    @Parameter(name = "persistence")
    private PersistenceConfiguration persistence = PersistenceConfiguration.DEFAULT_CONFIG;

    @Override
    public void execute() throws MojoExecutionException {
        try (final SearchPlatform platform = new ApacheSolr()) {
            final Engine engine = new Engine(
                    platform,
                    configurationsFolder,
                    corporaFolder,
                    ratingsFolder,
                    templatesFolder,
                    new SimpleMetricClassManager(metrics),
                    fields.split(","),
                    exclude,
                    include,
                    checksumFile,
                    persistence);

            final Map<String, Object> configuration = new HashMap<>();
            if (dataFolder != null && !dataFolder.isEmpty()) {
                configuration.put("solr.home", dataFolder);
            }
            configuration.put("forceRefresh", forceRefresh);

            engine.evaluate(configuration);
        } catch (final IOException exception) {
            throw new MojoExecutionException(exception.getMessage(), exception);
        }
    }
}