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
