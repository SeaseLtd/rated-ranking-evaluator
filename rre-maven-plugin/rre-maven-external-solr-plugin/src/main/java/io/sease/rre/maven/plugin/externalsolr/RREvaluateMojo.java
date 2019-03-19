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
package io.sease.rre.maven.plugin.externalsolr;

import io.sease.rre.core.Engine;
import io.sease.rre.core.domain.metrics.MetricClassManager;
import io.sease.rre.core.domain.metrics.ParameterizedMetricClassManager;
import io.sease.rre.core.domain.metrics.SimpleMetricClassManager;
import io.sease.rre.core.evaluation.EvaluationConfiguration;
import io.sease.rre.persistence.PersistenceConfiguration;
import io.sease.rre.search.api.SearchPlatform;
import io.sease.rre.search.api.impl.ExternalApacheSolr;
import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;

import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * RREvalutation Mojo (External Apache Solr binding).
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
@Mojo(name = "evaluate", inheritByDefault = false, defaultPhase = LifecyclePhase.PACKAGE)
public class RREvaluateMojo extends AbstractMojo {

    @Parameter(name = "configurations-folder", defaultValue = "${basedir}/src/etc/configuration_sets")
    private String configurationsFolder;

    @Parameter(name = "ratings-folder", defaultValue = "${basedir}/src/etc/ratings)")
    private String ratingsFolder;

    @Parameter(name = "templates-folder", defaultValue = "${basedir}/src/etc/templates")
    private String templatesFolder;

    @Parameter(name = "metrics", defaultValue = "io.sease.rre.core.domain.metrics.impl.PrecisionAtOne,io.sease.rre.core.domain.metrics.impl.PrecisionAtTwo,io.sease.rre.core.domain.metrics.impl.PrecisionAtThree,io.sease.rre.core.domain.metrics.impl.PrecisionAtTen")
    private List<String> metrics;

    @Parameter(name = "parameterizedMetrics")
    private Map<String, Map> parameterizedMetrics;

    @Parameter(name = "fields", defaultValue = "*,score")
    private String fields;

    @Parameter(name = "include")
    private List<String> include;

    @Parameter(name = "exclude")
    private List<String> exclude;

    @Parameter(name = "persistence")
    private PersistenceConfiguration persistence = PersistenceConfiguration.DEFAULT_CONFIG;

    @Parameter(name = "evaluation")
    private EvaluationConfiguration evaluation = EvaluationConfiguration.DEFAULT_CONFIG;

    @Override
    public void execute() throws MojoExecutionException {
        try (final SearchPlatform platform = new ExternalApacheSolr()) {
            final MetricClassManager metricClassManager =
                    parameterizedMetrics == null ? new SimpleMetricClassManager(metrics) : new ParameterizedMetricClassManager(metrics, parameterizedMetrics);
            final Engine engine = new Engine(
                    platform,
                    configurationsFolder,
                    null,
                    ratingsFolder,
                    templatesFolder,
                    metricClassManager,
                    fields.split(","),
                    exclude,
                    include,
                    null,
                    persistence,
                    evaluation);

            final Map<String, Object> configuration = Collections.emptyMap();

            engine.evaluate(configuration);
        } catch (final IOException exception) {
            throw new MojoExecutionException(exception.getMessage(), exception);
        }
    }
}