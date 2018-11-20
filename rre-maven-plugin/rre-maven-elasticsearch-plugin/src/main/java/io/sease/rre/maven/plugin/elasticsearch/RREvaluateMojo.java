package io.sease.rre.maven.plugin.elasticsearch;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.Engine;
import io.sease.rre.core.domain.Evaluation;
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

import static java.util.Optional.ofNullable;

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

    @Parameter(name = "metrics", defaultValue = "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne,io.sease.rre.core.domain.metrics.impl.PrecisionAtTwo,io.sease.rre.core.domain.metrics.impl.PrecisionAtThree,io.sease.rre.core.domain.metrics.impl.PrecisionAtTen")
    private List<String> metrics;

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
            final Engine engine = new Engine(
                    platform,
                    configurationsFolder,
                    corporaFolder,
                    ratingsFolder,
                    templatesFolder,
                    metrics,
                    fields.split(","),
                    exclude,
                    include,
                    persistence);

            final Map<String, Object> configuration = new HashMap<>();
            configuration.put("path.home", "/tmp");
            configuration.put("network.host", port);
            configuration.put("plugins", plugins);

            write(engine.evaluate(configuration));
        } catch (final IOException exception) {
            throw new MojoExecutionException(exception.getMessage(), exception);
        }
    }

    /**
     * Writes out the evaluation result.
     *
     * @param evaluation the evaluation result.
     * @throws IOException in case of I/O failure.
     */
    private void write(final Evaluation evaluation) throws IOException {
        final File outputFolder = new File("target/rre");
        outputFolder.mkdirs();

        final ObjectMapper mapper = new ObjectMapper();
        mapper.writerWithDefaultPrettyPrinter().writeValue(new File(outputFolder, "evaluation.json"), evaluation);
    }

    PersistenceConfiguration getPersistence() {
        return persistence;
//        return ofNullable(persistence).orElse(PersistenceConfiguration.defaultConfiguration());
    }
}