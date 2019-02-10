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
package io.sease.rre.persistence;

import io.sease.rre.core.domain.Query;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

/**
 * The general manager class for all persistence handlers. This provides
 * methods for starting, processing, and shutting down a number of handlers
 * via single method calls.
 * <p>
 * Persistence handlers should be constructed outside the manager, including
 * any required initialisation via the {@link PersistenceHandler#configure(String, Map)}
 * method, then registered using {@link #registerHandler(PersistenceHandler)}.
 * <p>
 * Most other methods apply to all registered handlers.
 *
 * @author Matt Pearce (matt@flax.co.uk)
 */
public class PersistenceManager {

    private static final Logger LOGGER = LogManager.getLogger(PersistenceManager.class);

    private final List<PersistenceHandler> handlers = new ArrayList<>();

    public void registerHandler(PersistenceHandler handler) {
        LOGGER.info("Registering handler " + handler.getName() + " -> " + handler.getClass().getCanonicalName());
        handlers.add(handler);
    }

    public void beforeStart() {
        for (Iterator<PersistenceHandler> it = handlers.iterator(); it.hasNext(); ) {
            PersistenceHandler h = it.next();
            try {
                h.beforeStart();
            } catch (PersistenceException e) {
                LOGGER.error("beforeStart failed for handler [" + h.getName() + "] :: " + e.getMessage());
                it.remove();
            }
        }

        // Check that there are handlers available
        checkHandlers();
    }

    public void start() {
        for (Iterator<PersistenceHandler> it = handlers.iterator(); it.hasNext(); ) {
            PersistenceHandler h = it.next();
            try {
                h.start();
            } catch (PersistenceException e) {
                LOGGER.error("[" + h.getName() + "] failed to start :: " + e.getMessage());
                it.remove();
            }
        }

        checkHandlers();
    }

    private void checkHandlers() {
        if (handlers.size() == 0) {
            throw new RuntimeException("No running persistence handlers!");
        }
    }

    public void recordQuery(Query query) {
        handlers.parallelStream().forEach(h -> h.recordQuery(query));
    }

    public void beforeStop() {
        handlers.parallelStream().forEach(PersistenceHandler::beforeStop);
    }

    public void stop() {
        handlers.parallelStream().forEach(PersistenceHandler::stop);
    }
}
