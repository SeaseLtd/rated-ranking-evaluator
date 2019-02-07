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
package io.sease.rre.maven.plugin.elasticsearch;

import io.sease.rre.persistence.PersistenceConfiguration;
import org.apache.maven.plugin.Mojo;
import org.apache.maven.plugin.testing.MojoRule;
import org.junit.Rule;
import org.junit.Test;

import static org.junit.Assert.*;

/**
 * Basic configuration tests for the ES Evaluate plugin.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class RREvaluateMojoTest {

    @Rule
    public MojoRule rule = new MojoRule()
    {
        @Override
        protected void before() throws Throwable
        {
        }

        @Override
        protected void after()
        {
        }
    };

    @Test
    public void testBuildsDefaultPersistenceConfig_whenNoPersistenceConfigInPom() throws Exception {
        Mojo mojo = rule.lookupMojo("evaluate", "src/test/resources/persistence/no_persistence_pom.xml");
        assertNotNull(mojo);

        RREvaluateMojo rreMojo = (RREvaluateMojo) mojo;
        PersistenceConfiguration persist = rreMojo.getPersistence();
        assertNotNull(persist);
        assertFalse(persist.isUseTimestampAsVersion());
        assertEquals(persist.getHandlers().size(), 1);
        assertTrue(persist.getHandlers().containsKey("json"));
        assertTrue(persist.getHandlerConfiguration().containsKey("json"));
    }

    @Test
    public void testBuildsCorrectPersistenceConfig_whenPersistenceConfigInPom() throws Exception {
        Mojo mojo = rule.lookupMojo("evaluate", "src/test/resources/persistence/persistence_pom.xml");
        assertNotNull(mojo);

        RREvaluateMojo rreMojo = (RREvaluateMojo) mojo;
        PersistenceConfiguration persist = rreMojo.getPersistence();
        assertNotNull(persist);
        assertTrue(persist.isUseTimestampAsVersion());
        assertEquals(persist.getHandlers().size(), 1);
        assertTrue(persist.getHandlers().containsKey("testJson"));
        assertTrue(persist.getHandlerConfiguration().containsKey("testJson"));
        assertNotNull(persist.getHandlerConfiguration().get("testJson"));
        assertEquals(persist.getHandlerConfiguration().get("testJson").get("destinationFile"), "blah.txt");
    }
}
