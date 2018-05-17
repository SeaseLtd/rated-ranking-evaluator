package io.sease.rre.maven.plugin.solr;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import static io.sease.rre.Utility.safe;

import com.fasterxml.jackson.databind.node.ObjectNode;
import io.sease.rre.search.api.SearchPlatform;
import io.sease.rre.search.api.impl.ApacheSolr;
import org.apache.maven.plugin.logging.Log;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.plugins.annotations.ResolutionScope;
import org.apache.maven.project.MavenProject;
import org.apache.maven.reporting.AbstractMavenReport;
import org.apache.maven.reporting.MavenReportException;
import org.apache.solr.client.solrj.util.ClientUtils;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Locale;
import java.util.Map;
import java.util.stream.StreamSupport;

import static java.util.Arrays.stream;

@Mojo(name = "rre", defaultPhase = LifecyclePhase.SITE, requiresDependencyResolution = ResolutionScope.RUNTIME, threadSafe = true)
public class RREReportingPlugin extends AbstractMavenReport {
    @Parameter(defaultValue = "${project}", readonly = true)
    private MavenProject project;

    @Parameter(defaultValue = "${basedir}/src/etc")
    private String rootFolder;

    @Parameter(name="configurations-folder", defaultValue = "${basedir}/src/etc/configurations")
    String configurationsFolderPath;

    @Parameter(name="collections-folder", defaultValue = "${basedir}/src/etc/datasets")
    String collectionsFolderPath;

    @Parameter(name="ratings-folder", defaultValue = "${basedir}/src/etc/ratings)")
    String ratingsFolderPath;

    @Parameter(name="templates-folder", defaultValue = "${basedir}/target")
    String targetFolderPath;

    @Parameter(name="target-folder", defaultValue = "${basedir}/src/etc/templates")
    String templatesFolderPath;

    @Override
    public boolean canGenerateReport() {
        if (!file(configurationsFolderPath).canRead()) {
            getLog().error("Unable to execute the evaluation: the configurations folder " + configurationsFolderPath + " doesn't exist or it's not readable.");
            return false;
        }

        if (!file(collectionsFolderPath).canRead()) {
            getLog().error("Unable to execute the evaluation: the collections folder " + collectionsFolderPath + " doesn't exist or it's not readable.");
            return false;
        }

        if (!file(ratingsFolderPath).canRead()) {
            getLog().error("Unable to execute the evaluation: the ratings folder " + ratingsFolderPath + " doesn't exist or it's not readable.");
            return false;
        }

        return true;
    }

    private File file(final String path) {
        return new File(path);
    }

    @Override
    protected void executeReport(final Locale locale) throws MavenReportException {
        final Log logger = getLog();

        try (final SearchPlatform platform = new ApacheSolr()) {
            final ObjectMapper mapper = new ObjectMapper();
            final JsonNode ratings = mapper.readTree(new File(file(ratingsFolderPath), "ratings.json"));

            final Map<String, Object> configuration = new HashMap<>();
            configuration.put("solr.home", "/tmp");

            platform.beforeStart(configuration);
            platform.start();
            platform.afterStart();

            final String coreName = ratings.get("index").asText();
            final File data = new File(file(collectionsFolderPath), ratings.get("collection_file").asText());
            if (!data.canRead()) {
                throw new IllegalArgumentException("Unable to read the collection file " + data.getAbsolutePath());
            }
            getLog().info("Something");

            stream(safe(file(configurationsFolderPath).listFiles()))
                    .flatMap(versionFolder -> stream(safe(versionFolder.listFiles())))
                    .filter(folder -> folder.getName().equals(coreName))
                    .forEach(folder -> {
                        final String version = folder.getParentFile().getName();
                        getLog().info("About to load the core \"" + coreName + "\" version " + version);
                        platform.load(data, folder, coreName + "_" + version);

                        StreamSupport.stream(ratings.get("information_needs").spliterator(), false)
                                .forEach(informationNeed -> {
                                    StreamSupport.stream(informationNeed.get("query_groups").spliterator(), false)
                                            .forEach(queryGroup -> {
                                                StreamSupport.stream(queryGroup.get("queries").spliterator(), false)
                                                        .forEach(query -> {
                                                            String queryTemplate = queryTemplate(query.get("template").asText());
                                                            for (final Iterator<String> iterator = query.get("placeholders").fieldNames(); iterator.hasNext();) {
                                                                final String name = iterator.next();
                                                                queryTemplate = queryTemplate.replace(name, query.get("placeholders").get(name).asText());
                                                            }
                                                            platform.executeQuery(coreName + "_" + version, queryTemplate);
                                                        });
                                            });
                                });
                    });

            platform.beforeStop();

        } catch (final IOException exception) {
            exception.printStackTrace();
            throw new MavenReportException(exception.getMessage());
        }

/*
        Sink mainSink = getSink();
        if (mainSink == null) {
            throw new MavenReportException("Could not get the Doxia sink");
        }

        // Page title
        mainSink.head();
        mainSink.title();
        mainSink.text("Simple Report for " + project.getName() + " " + project.getVersion());
        mainSink.title_();
        mainSink.head_();

        mainSink.body();

        // Heading 1
        mainSink.section1();
        mainSink.sectionTitle1();
        mainSink.text("Simple Report for " + project.getName() + " " + project.getVersion());
        mainSink.sectionTitle1_();

        // Content
        mainSink.paragraph();
        mainSink.text("This page provides simple information, like its location: ");
        mainSink.text(project.getBasedir().getAbsolutePath());
        mainSink.paragraph_();

        // Close
        mainSink.section1_();
        mainSink.body_();
*/
    }

    @Override
    public String getOutputName() {
        return "rre-report";
    }

    @Override
    public String getName(final Locale locale) {
        return "Relevancy & Ranking Evaluation Reporting Plugin";
    }

    @Override
    public String getDescription(Locale locale) {
        return null;
    }

    private JsonNode payload(final File file) {
        final ObjectMapper mapper = new ObjectMapper();
        try {
            return mapper.readTree(file);
        } catch (IOException exception) {
           throw new IllegalArgumentException(exception);
        }
    }

    private String queryTemplate(final String templateName) {
        try {
            return new String(Files.readAllBytes(new File(templatesFolderPath, templateName).toPath()));
        } catch (final Exception exception) {
            throw new RuntimeException(exception);
        }
    }
}
