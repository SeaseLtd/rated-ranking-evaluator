# Elasticsearch Persistence plugin

This persistence plugin enables RRE to write its output to an Elasticsearch
instance.

Query results are temporarily stored in memory, before being sent to
Elasticsearch in batches. This happens in parallel with the evaluation
process, with results being stored continuously as it progresses.

The queries themselves are flattened, so that one document is created for
each configuration set the query is run against. In other words, if you
have three configuration versions, each query will generate three
Elasticsearch documents, each with the metrics for one version.


## Usage (Maven)

To use, the module needs to be included in the dependencies for the RRE
plugin. In addition, two other dependency libraries must also be added -
the Elasticsearch connector requires some specific library versions, and
the Maven defaults are (currently) older than the minimum required.

Add the following to the `pom.xml`:

```
<build>
  <plugins>
    <plugin>
      <groupId>io.sease</groupId>
      <artifactId>rre-maven-elasticsearch-plugin</artifactId>
      <version>${elasticsearch.version}</version>
      <dependencies>
        <dependency>
          <groupId>io.sease</groupId>
          <artifactId>rre-persistence-plugin-elasticsearch</artifactId>
          <version>${elasticsearch.version}</version>
        </dependency>
        <dependency>
          <groupId>org.apache.httpcomponents</groupId>
          <artifactId>httpcore</artifactId>
          <version>4.4.5</version>
        </dependency>
        <dependency>
          <groupId>org.apache.httpcomponents</groupId>
          <artifactId>httpclient</artifactId>
          <version>4.5.2</version>
        </dependency>
      </dependencies>
      <configuration>
        ... other configuration ...
        <port>9220</port>
        <persistence>
          <handlers>
            <elasticsearch>io.sease.rre.persistence.impl.ElasticsearchPersistenceHandler</elasticsearch>
          </handlers>
          <handlerConfiguration>
            <elasticsearch>
              <index>rre_evaluation</index>
              <baseUrl>
                <param>http://elastic1:9200</param>
                <param>http://elastic2:9200</param>
              </baseUrl>
            </elasticsearch>
          </handlerConfiguration>
        </persistence>
      </configuration>
      ...
    </plugin>
  </plugins>
</build>
```

Note that if you are using the Elasticsearch RRE plugin with a local
Elasticsearch instance, you will need to set the `port` configuration option
to something that isn't in use by your local Elasticsearch.


## Configuration options

There are a number of configuration options that can be set to tune
performance if necessary:

- `index` **[REQUIRED]** - the name of the index the evaluation results
should be written to.
- `baseUrl` - the base Elasticsearch URL that should be used. This can either
be a list or a single URL. Default: http://localhost:9200
- `threadpoolSize` - the maximum number of threads available to store data to
Elasticsearch. Default: 2
- `runIntervalMs` - how long the persistence handler should wait between
sending batches of documents (in milliseconds). Default: 500
- `batchSize` - the maximum number of queries that will be handled in a
single batch. This may not be the same as the number of documents being
stored in Elasticsearch, since the queries are flattened out, creating
one document per config version. Default: 500

The output index will be created if it does not already exist, using a
pre-configured mapping file.


## Output documents

The output documents look as follows:

```
{
  "id": "3e809be357848326fe32cbe6ee626431",
  "corpora": "electric_basses.bulk",
  "topic": "Fender basses",
  "queryGroup": "The group tests several searches on the Fender brand",
  "queryText": "Fender bass",
  "version": "v1.1",
  "totalHits": 2,
  "metrics": [
    {
      "name": "P",
      "sanitisedName": "p",
      "value": 1
    },
    {
      "name": "R",
      "sanitisedName": "r",
      "value": 1
    },
    {
      "name": "P@3",
      "sanitisedName": "pAt3",
      "value": 1
    },
    {
      "name": "NDCG@10",
      "sanitisedName": "ndcgAt10",
      "value": 1
    },
    {
      "name": "P@10",
      "sanitisedName": "pAt10",
      "value": 1
    },
    {
      "name": "RR@10",
      "sanitisedName": "rrAt10",
      "value": 1
    },
    {
      "name": "P@2",
      "sanitisedName": "pAt2",
      "value": 1
    },
    {
      "name": "P@1",
      "sanitisedName": "pAt1",
      "value": 1
    },
    {
      "name": "AP",
      "sanitisedName": "ap",
      "value": 1
    }
  ],
  "metricValues": {
    "p": 1,
    "r": 1,
    "pAt3": 1,
    "ndcgAt10": 1,
    "pAt10": 1,
    "pAt2": 1,
    "rrAt10": 1,
    "pAt1": 1,
    "ap": 1
  },
  "results": [
    ... result content ...
  ]
}
```

The `metricValues` map contains the metric value outputs, using sanitised
versions of the metric names (so NDCG@10 is `ndcgAt10`, and so on). The
document ID is generated from the corpus, topic, query group, query text
and version, so can be regenerated easily to overwrite the documents when
running multiple times.

Note that the `metrics` structure is **not** nested in the index. Kibana has
no option for using nested structures when generating output, so the
`metricValues` mapping should be used instead. This only contains the output
for each metric. Values can be referenced using `metricValues.p`,
`metricValues.r`, and so on.

The `results` field is present to allow checking of the result data returned
by the searches. If using the default configuration, the field mapping is set
to `enabled: false`, meaning that all content is stored but not indexed, and
therefore is not searchable.