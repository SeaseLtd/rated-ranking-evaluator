package io.sease.rre.core.domain;

import io.sease.rre.search.api.SearchPlatform;

import java.io.File;

public class Suite extends DomainMember {
    private final SearchPlatform platform;

    public Suite(SearchPlatform platform) {
        this.platform = platform;
    }
}