/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package io.sease.rre.search.api.impl;

import org.apache.solr.client.solrj.SolrServer;
import org.apache.solr.client.solrj.impl.CloudSolrServer;
import org.apache.solr.client.solrj.impl.HttpSolrServer;
import org.apache.solr.client.solrj.impl.LBHttpSolrServer;

import java.io.Closeable;
import java.util.HashMap;
import java.util.Map;
import java.util.StringJoiner;

import static java.util.Optional.ofNullable;

/**
 * Manager class for Solr Clients in use when connecting to external Solr instances.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
class SolrClientManager implements Closeable {

    private final Map<String, SolrServer> indexClients = new HashMap<>();

    /**
     * Build a SolrClient instance, associating it with a specific target index
     * (or core).
     *
     * @param targetIndexName the name of the index/core this client should be
     *                        used with.
     * @param settings        the {@link io.sease.rre.search.api.impl.ExternalApacheSolr.SolrSettings}
     *                        containing the client connection details.
     */
    void buildSolrClient(String targetIndexName, ExternalApacheSolr.SolrSettings settings) {
        SolrServer client;

        if (settings.hasZookeeperSettings()) {
            final StringJoiner joiner = new StringJoiner(",");
            settings.getZkHosts().forEach(joiner::add);

            final CloudSolrServer solr = new CloudSolrServer(joiner.toString());
            client = solr;
        } else if (settings.getBaseUrls().size() > 1) {
            try {
                final LBHttpSolrServer solr = new LBHttpSolrServer(settings.getBaseUrls().toArray(new String[0]));
                solr.setConnectionTimeout(settings.getConnectionTimeout());
                solr.setSoTimeout(settings.getSocketTimeout());
                client = solr;
            } catch (Exception exception) {
                HttpSolrServer solr = new HttpSolrServer(settings.getBaseUrls().get(0));
                solr.setConnectionTimeout(settings.getConnectionTimeout());
                solr.setSoTimeout(settings.getSocketTimeout());
                client = solr;
            }
        } else {
            HttpSolrServer solr = new HttpSolrServer(settings.getBaseUrls().iterator().next());
            ofNullable(settings.getConnectionTimeout()).ifPresent(solr::setConnectionTimeout);
            ofNullable(settings.getSocketTimeout()).ifPresent(solr::setSoTimeout);
            client = solr;
        }

        indexClients.put(targetIndexName, client);
    }

    /**
     * Get the SolrClient for a specific target index.
     *
     * @param targetIndexName the name of the index/core whose client is
     *                        required.
     * @return the client, or {@code null} if no client has been set for the
     * target index.
     */
    SolrServer getSolrClient(String targetIndexName) {
        return indexClients.get(targetIndexName);
    }

    /**
     * Ensure that all of the index clients are closed.
     */
    public void close() {
        indexClients.values().forEach(SolrServer::shutdown);
    }
}
