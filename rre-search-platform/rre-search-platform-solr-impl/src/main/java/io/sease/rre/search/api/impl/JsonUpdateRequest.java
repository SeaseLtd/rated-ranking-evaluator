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
