package io.sease.rre.maven.plugin.report;

import org.apache.maven.reporting.MavenReportException;

import java.io.File;
import java.util.Collections;
import java.util.Locale;

import static java.util.Arrays.asList;

public class Main {
    public static void main(String a []) throws Exception {
        RREReport report = new RREReport(){
            @Override
            File evaluationOutputFile() {
                return new File("/Users/agazzarini/workspaces/rated-ranking-evaluator/rre-maven-plugin/rre-maven-solr-plugin/target/rre/evaluation.json");
            }

            @Override
            public String getOutputName() {
                return "rre-report";
            }
        };

        report.setReportOutputDirectory(new File("/Users/agazzarini/workspaces/rated-ranking-evaluator/rre-maven-plugin/rre-maven-solr-plugin/target/rre"));
        report.formats = Collections.singletonList("spreadsheet");

        report.executeReport(Locale.getDefault());
    }
}
