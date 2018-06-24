package io.sease.rre.maven.plugin.solr;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.core.Engine;
import io.sease.rre.core.domain.Evaluation;
import io.sease.rre.search.api.SearchPlatform;
import io.sease.rre.search.api.impl.ApacheSolr;
import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugins.annotations.Execute;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;

import java.io.File;
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
@Mojo( name = "evaluate", inheritByDefault = false, defaultPhase = LifecyclePhase.PACKAGE)
public class RREvaluateMojo extends AbstractMojo {

    @Parameter(name="configurations-folder", defaultValue = "${basedir}/src/etc/configuration_sets")
    private String configurationsFolder;

    @Parameter(name="corpora-folder", defaultValue = "${basedir}/src/etc/corpora")
    private String corporaFolder;

    @Parameter(name="ratings-folder", defaultValue = "${basedir}/src/etc/ratings)")
    private String ratingsFolder;

    @Parameter(name="templates-folder", defaultValue = "${basedir}/src/etc/templates")
    private String templatesFolder;

    @Parameter(name="metrics", defaultValue = "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne,io.sease.rre.core.domain.metrics.impl.PrecisionAtTwo,io.sease.rre.core.domain.metrics.impl.PrecisionAtThree,io.sease.rre.core.domain.metrics.impl.PrecisionAtTen")
    private List<String> metrics;

    @Parameter(name="fields", defaultValue = "*,score")
    private String fields;

    @Override
    public void execute() throws MojoExecutionException {
        try (final SearchPlatform platform = new ApacheSolr()) {
            final Engine engine = new Engine(
                platform,
                configurationsFolder,
                    corporaFolder,
                    ratingsFolder,
                    templatesFolder,
                    metrics,
                    fields.split(","));

            final Map<String, Object> configuration = new HashMap<>();
            configuration.put("solr.home", "/tmp");

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
}