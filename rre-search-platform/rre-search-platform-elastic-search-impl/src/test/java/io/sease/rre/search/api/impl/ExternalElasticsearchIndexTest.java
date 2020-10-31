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

import io.sease.rre.search.api.SearchPlatform;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.mockserver.client.MockServerClient;
import org.mockserver.junit.MockServerRule;

import java.util.Collections;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.mockserver.model.HttpRequest.request;
import static org.mockserver.model.HttpResponse.response;


/**
 * An integration test for checking ExternalElasticsearch methods that rely on
 * an existing Elasticsearch cluster.
 *
 * @author Matt Pearce (matt@elysiansoftware.co.uk)
 */
public class ExternalElasticsearchIndexTest {

	private static final String INDEX_NAME = "test";
	private static final String VERSION = "1.0";

	private static final String ES_DOCKER_IMAGE = "docker.elastic.co/elasticsearch/elasticsearch";
	private static final String ES_VERSION = "7.5.0";

	@Rule
	public TemporaryFolder tempFolder = new TemporaryFolder();
	@Rule
	public MockServerRule mockServerRule = new MockServerRule(this);

	private MockServerClient mockServerClient;

	private SearchPlatform platform;

	@Before
	public void setupPlatform() throws Exception {
		platform = new ExternalElasticsearch();
		// Setting these explicitly, rather than using load()
		((ExternalElasticsearch) platform).setSettings(
				new ExternalElasticsearch.IndexSettings(Collections.singletonList("http://localhost:" + mockServerClient.getPort()), null, null),
				VERSION);
	}

	@Test
	public void checkCollection_returnsFalseWhenNotLoaded() throws Exception {
		mockServerClient.when(request().withMethod("HEAD").withPath("/" + INDEX_NAME))
				.respond(response().withStatusCode(404));
		assertFalse(platform.checkCollection(INDEX_NAME, VERSION));
	}

	@Test
	public void checkCollection_returnsTrueWhenAvailable() throws Exception {
		mockServerClient.when(request().withMethod("HEAD").withPath("/" + INDEX_NAME))
				.respond(response().withStatusCode(200));
		assertTrue(platform.checkCollection(INDEX_NAME, VERSION));
	}
}
