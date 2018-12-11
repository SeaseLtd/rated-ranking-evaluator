# Persistence plugins

This directory holds the persistence framework plugins.


## Configuration (Maven)

Configuration for the persistence framework is optional. By default it will
behave exactly as it did before the framework was added - a JSON file will be
generated, which can be read by the report plugin and used to create a
spreadsheet or feed the rre-server.

If you do choose to use additional persistence plugins, the extra
configuration looks like this:

```
<build>
  <plugins>
    <plugin>
      <!-- Elasticsearch evaluation plugin -->
      <groupId>io.sease</groupId>
      <artifactId>rre-maven-elasticsearch-plugin</artifactId>
      <version>${elasticsearch.version}</version>
      <dependencies>
        <!-- Each additional persistence plugin needs to be defined here -->
        <!-- Dependency for Elasticsearch persistence -->
        <dependency>
          <groupId>io.sease</groupId>
          <artifactId>rre-persistence-plugin-elasticsearch</artifactId>
          <version>${elasticsearch.version}</version>
        </dependency>
      </dependencies>
      <configuration>
        ... main plugin configuration ...
        <persistence>
          <handlers>
            <!-- Define each handler implementation with a name -->
            <json>io.sease.rre.persitence.impl.JsonPersistenceHandler</json>
            <es_local>io.sease.rre.persistence.impl.ElasticsearchPersistenceHandler</es_local>
            <es_shared>io.sease.rre.persistence.impl.ElasticsearchPersistenceHandler</es_shared>
          </handlers>
          <handlerConfiguration>
            <!-- Add the configuration for each handler, using its name -->
            <json><!-- Any non-default JSON config --></json>
            <es_local>
              <index>rre_evaluation</index>
              ... further elasticsearch configuration ...
            </es_local>
            <es_shared>
              <index>rre_evaluation</index>
              <baseUrl>http://elastic1:9200</baseUrl>
              ... further es_shared configuration ...
            </es_shared>
          </handlerConfiguration>
        </persistence>
      </configuration>
      ...
    </plugin>
  </plugins>
</build>
```

As shown above, there is a new `persistence` section in the
configuration, which can be broken down into two main sections:

- `handlers`, where each handler is defined using a name, and the
implementing class. The name can be any value, allowing the same
implementation to be used multiple times, if necessary.

- `handlerConfiguration`, containing the configuration for each handler. This
is broken into blocks, using the handler name defined in the `handlers`
section.


## Output to JSON

The default persistence implementation is to write to a JSON file. With no
additional configuration, this will write to the `target/rre/evaluation.json`,
as before the implementation of the framework.

The JSON persistence handler has the following configuration options:

- `destinationFile` - the file the evaluation output should be written to.
Default: target/rre/evaluation.json
- `pretty` - should the JSON be written using a prettified formatter, where
lines are indented, etc. This makes the output more human-readable, but also
makes it larger. Default: false

Note that if the destination file is changed and you are using the reporting
plugin, you will need to set the `evaluationFile` parameter in the report
plugin configuration to point to your output file.