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

import io.sease.rre.search.api.QueryOrSearchResponse;
import io.sease.rre.search.api.SearchPlatform;
import org.apache.solr.client.solrj.SolrClient;
import org.apache.solr.client.solrj.impl.HttpSolrClient;
import org.apache.solr.common.SolrInputDocument;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.testcontainers.containers.SolrContainer;
import org.testcontainers.utility.DockerImageName;

import java.io.File;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * Integration tests for the Solr implementation.
 * <p>
 * These won't be run as part of the main test phase, only as part of the
 * "integration" profile.
 * <p>
 * These use the TestContainers framework, which spins up Docker containers
 * to allow testing against a Solr instance.
 *
 * @author Matt Pearce (matt@elysiansoftware.co.uk)
 */
public class ExternalApacheSolrIT {

	private static final String SOLR_CONTAINER_BASE = "solr";
	private static final String DEFAULT_SOLR_VERSION = "8.6";

	private static final String INDEX_NAME = "test";
	private static final String INDEX_VERSION = "v1.0";

	private static final DockerImageName DOCKER_IMAGE = DockerImageName.parse(SOLR_CONTAINER_BASE + ":" + System.getProperty("solr.version", DEFAULT_SOLR_VERSION));

	@Rule
	public TemporaryFolder tempFolder = new TemporaryFolder();

	private SearchPlatform platform;

	@Before
	public void setupPlatform() {
		platform = new ExternalApacheSolr();
	}

	@Test
	public void checkCollectionReturnsFalse_whenNoSuchCollection() throws Exception {
		final SolrContainer solrContainer = new SolrContainer(DOCKER_IMAGE);
		solrContainer.start();

		final File settingsFile = tempFolder.newFile("ccrf_settings.json");
		FileWriter fw = new FileWriter(settingsFile);
		fw.write("{ \"baseUrls\": [ \"http://" + solrContainer.getHost() + ":" + solrContainer.getSolrPort() + "\" ]}");
		fw.close();

		platform.load(null, settingsFile, INDEX_NAME, INDEX_VERSION);

		assertFalse(platform.checkCollection(INDEX_NAME, INDEX_VERSION));
		solrContainer.close();
	}

	@Test
	public void checkCollectionReturnsTrue_whenCollectionExists() throws Exception {
		final SolrContainer solrContainer = new SolrContainer(DOCKER_IMAGE).withCollection(INDEX_NAME);
		solrContainer.start();

		final File settingsFile = tempFolder.newFile("ccrt_settings.json");
		FileWriter fw = new FileWriter(settingsFile);
		fw.write("{ \"baseUrls\": [ \"http://" + solrContainer.getHost() + ":" + solrContainer.getSolrPort() + "/solr\" ]}");
		fw.close();

		platform.load(null, settingsFile, INDEX_NAME, INDEX_VERSION);

		assertTrue(platform.checkCollection(INDEX_NAME, INDEX_VERSION));
		solrContainer.close();
	}

	@Test
	public void checkCollection_allowsCollectionOverride() throws Exception {
		final String overrideCollection = "override";

		final SolrContainer solrContainer = new SolrContainer(DOCKER_IMAGE).withCollection(overrideCollection);
		solrContainer.start();

		final File settingsFile = tempFolder.newFile("ccaco_settings.json");
		FileWriter fw = new FileWriter(settingsFile);
		fw.write("{ \"baseUrls\": [ \"http://" + solrContainer.getHost() + ":" + solrContainer.getSolrPort() + "/solr\" ], \"collectionName\": \"" + overrideCollection + "\" }");
		fw.close();

		platform.load(null, settingsFile, INDEX_NAME, INDEX_VERSION);

		assertTrue(platform.checkCollection(INDEX_NAME, INDEX_VERSION));
		solrContainer.close();
	}


	@Test
    public void executeQuery_returnsResults() throws Exception {
	    final int numDocs = new Random().nextInt(10);

        final SolrContainer solrContainer = new SolrContainer(DOCKER_IMAGE).withCollection(INDEX_NAME);
        solrContainer.start();

        // Index some documents
        createDocuments(solrContainer.getHost(), solrContainer.getSolrPort(), INDEX_NAME, numDocs);

        final File settingsFile = tempFolder.newFile("eq_settings.json");
        FileWriter fw = new FileWriter(settingsFile);
        fw.write("{ \"baseUrls\": [ \"http://" + solrContainer.getHost() + ":" + solrContainer.getSolrPort() + "/solr\" ]}");
        fw.close();

        platform.load(null, settingsFile, INDEX_NAME, INDEX_VERSION);

        QueryOrSearchResponse response = platform.executeQuery(INDEX_NAME, INDEX_VERSION, "{ \"q\": \"*:*\" }", new String[]{ "id", "title_s" }, 10);

        assertEquals(numDocs, response.totalHits());
        solrContainer.close();
    }

    @Test
    public void executeQuery_allowsOverride() throws Exception {
        final int numDocs = new Random().nextInt(10);
        final String overrideCollection = "override";

        final SolrContainer solrContainer = new SolrContainer(DOCKER_IMAGE).withCollection(overrideCollection);
        solrContainer.start();

        // Index some documents
        createDocuments(solrContainer.getHost(), solrContainer.getSolrPort(), overrideCollection, numDocs);

        final File settingsFile = tempFolder.newFile("eqao_settings.json");
        FileWriter fw = new FileWriter(settingsFile);
        fw.write("{ \"baseUrls\": [ \"http://" + solrContainer.getHost() + ":" + solrContainer.getSolrPort() + "/solr\" ], \"collectionName\": \"" + overrideCollection + "\" }");
        fw.close();

        platform.load(null, settingsFile, INDEX_NAME, INDEX_VERSION);

        QueryOrSearchResponse response = platform.executeQuery(INDEX_NAME, INDEX_VERSION, "{ \"q\": \"*:*\" }", new String[]{ "id", "title_s" }, 10);

        assertEquals(numDocs, response.totalHits());
        solrContainer.close();
    }

    private void createDocuments(String solrHost, int solrPort, String collection, int numDocs) throws Exception {
        List<SolrInputDocument> docs = new ArrayList<>(numDocs);
	    for (int i = 0; i < numDocs; i ++) {
	        SolrInputDocument doc = new SolrInputDocument();
	        doc.addField("id", "" + i);
	        doc.addField("title_s", "Test");
	        docs.add(doc);
        }

	    final SolrClient client = new HttpSolrClient.Builder("http://" + solrHost + ":" + solrPort + "/solr").build();
	    client.add(collection, docs);
	    client.commit(collection);
    }
}
