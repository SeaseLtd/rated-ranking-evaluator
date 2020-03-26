package io.sease.rre.maven.plugin.evaluation;

import org.apache.maven.plugin.Mojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugin.testing.MojoRule;
import org.junit.Rule;
import org.junit.Test;

import static org.junit.Assert.*;


/**
 * Unit tests for the generic evaluation Maven plugin.
 *
 * @author Matt Pearce (mpearce@opensourceconnections.com)
 */
public class RREvaluateMojoTest {

    @Rule
    public MojoRule rule = new MojoRule() {
        @Override
        protected void before() {
        }

        @Override
        protected void after() {
        }
    };

    @Test
    public void throwsMojoException_whenSearchPlatformNotFound() throws Exception {
        Mojo mojo = rule.lookupMojo("evaluate", "src/test/resources/evaluateMojoTests/bad_searchplatform_pom.xml");
        assertNotNull(mojo);

        try {
            mojo.execute();
            fail("Expected MojoExecutionException");
        } catch (MojoExecutionException e) {
            assertTrue(e.getCause() instanceof ClassNotFoundException);
        }
    }

    @Test
    public void throwsMojoException_whenSearchPlatformCannotBeConstructed() throws Exception {
        Mojo mojo = rule.lookupMojo("evaluate", "src/test/resources/evaluateMojoTests/searchplatform_args_constructor_pom.xml");
        assertNotNull(mojo);

        try {
            mojo.execute();
            fail("Expected MojoExecutionException");
        } catch (MojoExecutionException e) {
            assertTrue(e.getCause() instanceof InstantiationException);
        }
    }
}
