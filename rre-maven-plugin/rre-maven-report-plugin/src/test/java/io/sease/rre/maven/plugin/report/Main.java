package io.sease.rre.maven.plugin.report;

import java.io.File;
import java.util.Locale;

import static java.util.Arrays.asList;

public class Main {
    public static void main(String a[]) throws Exception {
        RREMavenReport report = new RREMavenReport() {
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
        report.formats = asList("spreadsheet", "rre-server");
        report.endpoint = "http://127.0.0.1:8080";
        report.executeReport(Locale.getDefault());
    }
}
