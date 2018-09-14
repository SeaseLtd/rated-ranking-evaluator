package io.sease.rre.search.api.impl;

import org.apache.solr.client.solrj.request.AbstractUpdateRequest;
import org.apache.solr.client.solrj.request.ContentStreamUpdateRequest;
import org.apache.solr.common.util.ContentStream;
import org.apache.solr.common.util.ContentStreamBase;

import java.io.InputStream;
import java.util.Collection;

import static java.util.Collections.singletonList;

public class JsonUpdateRequest extends ContentStreamUpdateRequest {
    private final InputStream stream;

    /**
     * Builds a new Update request with the given (JSON) payload stream.
     *
     * @param stream the data stream.
     */
    public JsonUpdateRequest(final InputStream stream) {
        super("/update");
        this.stream = stream;
        this.setAction(ACTION.COMMIT, true, true);
    }

    @Override
    public Collection<ContentStream> getContentStreams() {
        return singletonList(new ContentStreamBase() {
            @Override
            public String getContentType() {
                return "application/json";
            }

            @Override
            public InputStream getStream() {
                return stream;
            }
        });
    }
}
