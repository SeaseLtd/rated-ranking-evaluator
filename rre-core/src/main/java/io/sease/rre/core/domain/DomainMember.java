package io.sease.rre.core.domain;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import java.util.stream.Stream;

/**
 * Supertype layer for all RRE domain entities.
 * It defines the common composite structure shared by all RRE entities.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class DomainMember<C extends DomainMember> {
    private String name;

    private Map<String, C> childrenLookupCache = new HashMap<>();

    private List<C> children = new ArrayList<>();

    /**
     * Adds the given child to this entity.
     *
     * @param child the child entity.
     */
    public C add(final C child) {
        children.add(child);
        return child;
    }

    public C findOrCreate(final String name, final Supplier<C> factory) {
        return add(childrenLookupCache.computeIfAbsent(name, key -> (C) factory.get().setName(name)));
    }

    public DomainMember setName(final String name) {
        this.name = name;
        return this;
    }

    /**
     * Returns the children stream.
     *
     * @return the children stream.
     */
    public Stream<C> childrenStream() {
        return children.stream();
    }

    /**
     * Returns the children of this entity.
     *
     * @return the children of this entity.
     */
    public List<C> getChildren() {
        return children;
    }

    /**
     * Returns the name of this entity.
     *
     * @return the name of this entity.
     */
    public String getName() {
        return name;
    }
}