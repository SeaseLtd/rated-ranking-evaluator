package io.sease.rre.maven.plugin.report;

import org.apache.maven.reporting.MavenReportException;

import java.io.File;
import java.util.Locale;

public class Main {
    public static void main(String a []) throws Exception {
        RREReport report = new RREReport(){
            @Override
            File evaluationOutputFile() {
                return new File("/Users/agazzarini/IdeaProjects/rated-ranking-evaluator/rre-maven-plugin/rre-maven-solr-plugin/target/rre/evaluation.json");
            }
        };

        report.executeReport(Locale.getDefault());
    }
}
