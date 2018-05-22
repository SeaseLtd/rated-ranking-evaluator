package io.sease.rre.core;

@FunctionalInterface
public interface EventCollector<T> {
    void collect(T event);
}
