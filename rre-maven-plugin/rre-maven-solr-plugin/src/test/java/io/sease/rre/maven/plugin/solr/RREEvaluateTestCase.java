package io.sease.rre.maven.plugin.solr;

import org.apache.maven.plugin.testing.AbstractMojoTestCase;

import java.io.File;

public class RREEvaluateTestCase extends AbstractMojoTestCase {
    @Override
    protected void setUp() throws Exception {
        super.setUp();
    }

    public void testMojoGoal() throws Exception {
        final File projectDefinition = new File( getBasedir(), "src/test/resources/pom.xml" );

        final RREvaluateMojo mojo =
                (RREvaluateMojo)configureMojo(
                    new RREvaluateMojo(),
                    extractPluginConfiguration("rre-maven-solr-plugin", projectDefinition));
        mojo.execute();
    }
}
