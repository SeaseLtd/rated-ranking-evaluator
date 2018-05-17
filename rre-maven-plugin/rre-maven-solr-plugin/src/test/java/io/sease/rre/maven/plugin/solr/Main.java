package io.sease.rre.maven.plugin.solr;

import java.util.Locale;

public class Main {
    public static void main(String args[]) throws Exception {
        RREReportingPlugin plugin = new RREReportingPlugin();
        plugin.ratingsFolderPath = "/Users/agazzarini/IdeaProjects/rr-evaluation-plugin/rre-search-platform/rre-search-platform-solr-impl/src/sample_solr_folders_layout/ratings";
        plugin.collectionsFolderPath="/Users/agazzarini/IdeaProjects/rr-evaluation-plugin/rre-search-platform/rre-search-platform-solr-impl/src/sample_solr_folders_layout/collection_sets";
        plugin.configurationsFolderPath="/Users/agazzarini/IdeaProjects/rr-evaluation-plugin/rre-search-platform/rre-search-platform-solr-impl/src/sample_solr_folders_layout/configuration_sets";
        plugin.templatesFolderPath="/Users/agazzarini/IdeaProjects/rr-evaluation-plugin/rre-search-platform/rre-search-platform-solr-impl/src/sample_solr_folders_layout/templates";
        plugin.executeReport(Locale.getDefault());
    }
}
