package io.sease.rre.core.domain;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

/**
 * Supertype layer for all RRE domain entities.
 * It defines the common composite structure shared by all RRE entities.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class DomainMember<T> {
    private String name;
    private List<T> children = new ArrayList<>();

    /**
     * Builds a new {@link DomainMember} instance with the given entity name or identifier.
     *
     * @param name the given entity name or identifier.
     */
    public DomainMember(final String name) {
        this.name = name;
    }

    /**
     * Adds the given child to this entity.
     *
     * @param child the child entity.
     */
    public T add(final T child) {
        children.add(child);
        return child;
    }

    /**
     * Returns the children stream.
     *
     * @return the children stream.
     */
    public Stream<T> childrenStream() {
        return children.stream();
    }

    /**
     * Returns the children of this entity.
     *
     * @return the children of this entity.
     */
    public List<T> getChildren() {
        return children;
    }
}