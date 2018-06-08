package io.sease.rre.maven.plugin.report.formats.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.sease.rre.maven.plugin.report.domain.EvaluationMetadata;
import io.sease.rre.maven.plugin.report.RREMavenReport;
import io.sease.rre.maven.plugin.report.formats.OutputFormat;
import okhttp3.*;

import java.util.Locale;

import static java.util.Objects.requireNonNull;

/**
 * OutputFormat implementor for sending evaluation results to a running RRE Server instance.
 * Clearly, this assumes you're using an RRE Server somewhere.
 *
 * @author agazzarini
 * @since 1.0
 */
public class RREOutputFormat implements OutputFormat {
    @Override
    public void writeReport(final JsonNode data, final EvaluationMetadata metadata, final Locale locale, final RREMavenReport plugin) {
        try {
            final ObjectMapper serializer = new ObjectMapper();
            Request request = new Request.Builder()
                    .url(requireNonNull(HttpUrl.parse(plugin.getEndpoint())))
                    .post(RequestBody.create(MediaType.parse("application/json"), serializer.writeValueAsString(data)))
                    .build();

            try (final Response response = new OkHttpClient().newCall(request).execute()) {
                if (response.code() != 200) {
                    System.out.println("Exception while communicating with RREServer. Return code was: " + response.code());
                } else {
                    System.out.println("Evaluation data has been correctly sent to RRE Server located at " + plugin.getEndpoint());
                }
            }
        } catch (final Exception exception) {
            exception.printStackTrace();
        }
    }
}
