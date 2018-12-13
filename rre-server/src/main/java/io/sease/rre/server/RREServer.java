package io.sease.rre.server;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.StandardEnvironment;

/**
 * RRE Server main entry point.
 *
 * @author agazzarini
 * @since 1.0
 */
@SpringBootApplication
public class RREServer {
    public static void main(final String[] args) {
        SpringApplication.run(RREServer.class, args);
    }
}