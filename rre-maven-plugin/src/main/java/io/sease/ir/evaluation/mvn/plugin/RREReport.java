package io.sease.ir.evaluation.mvn.plugin;

import org.apache.maven.doxia.sink.Sink;
import org.apache.maven.plugin.logging.Log;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.plugins.annotations.ResolutionScope;
import org.apache.maven.project.MavenProject;
import org.apache.maven.reporting.AbstractMavenReport;
import org.apache.maven.reporting.MavenReportException;

import java.util.Locale;
@Mojo(name = "rre", defaultPhase = LifecyclePhase.SITE, requiresDependencyResolution = ResolutionScope.RUNTIME, threadSafe = true)
public class RREReport extends AbstractMavenReport {
    @Parameter(defaultValue = "${project}", readonly = true)
    private MavenProject project;

    @Parameter(defaultValue = "${basedir}/src/etc")
    private String rootFolder;

    @Parameter(name="target-system-type", required = true)
    private String targetSystemType;

    @Parameter(name="target-system-version", required = true)
    private String targetSystemVersion;

    @Parameter(name="settings-folder", defaultValue = "${basedir}/src/etc/settings)")
    private String settings;

    @Parameter(name="datasets-folder", defaultValue = "${basedir}/src/etc/datasets)")
    private String datasets;

    @Override
    protected void executeReport(final Locale locale) throws MavenReportException {
        // Get the logger
        final Log logger = getLog();




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
}
