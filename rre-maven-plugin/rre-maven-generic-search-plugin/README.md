Generic Maven Search plugin
===============================

This search plugin allows the use of alternative search APIs other than the
supplied Solr and Elasticsearch choices.


## Archetype Usage

An example `pom.xml`, excluding most RRE configuration, would look like:

```
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany</groupId>
    <artifactId>my-evaluation-project</artifactId>
    <version>1.1</version>
    <packaging>pom</packaging>


    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
        <rre.version>1.1</rre.version>
    </properties>

    <pluginRepositories>
       <pluginRepository>
          <id>sease</id>
          <url>https://raw.github.com/SeaseLtd/rated-ranking-evaluator/mvn-repo</url>
       </pluginRepository>
    </pluginRepositories>

    <build>
        <plugins>
            <plugin>
                <groupId>io.sease</groupId>
                <artifactId>rre-maven-generic-search-plugin</artifactId>
                <version>${rre.version}</version>
                <!-- Dependency on your SearchPlatform implementation -->
                <dependency>
                    <groupId>com.mycompany</groupId>
                    <artifactId>my-rre-searchplatform</artifactId>
                    <version>1.1</version>
                </dependency>
                <configuration>
                    <!-- Provide class details for the SearchPlatform implementation -->
                    <searchPlatform>com.mycompany.search.MySearchPlatform</searchPlatform>
                    <!-- Provide any addition SearchPlatform configuration -->
                    <searchPlatformConfiguration>
                        <exampleConfigItem>... config details ...</exampleConfigItem>
                    </searchPlatformConfiguration>
                    <!-- Remaining RRE configuration below ... -->
                </configuration>
                <executions>
                    <execution>
                        <id>search-quality-evaluation</id>
                        <phase>package</phase>
                        <goals>
                            <goal>evaluate</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```


## Implementing SearchPlatform

To supply your own search platform, you need to implement the
[SearchPlatform](https://github.com/SeaseLtd/rated-ranking-evaluator/blob/master/rre-search-platform/rre-search-platform-api/src/main/java/io/sease/rre/search/api/SearchPlatform.java)
interface, which provides the connection between RRE and your search engine.
Your implementation should have a zero-argument constructor - the
configuration properties (set in the `searchPlatformConfiguration` block
in your pom.xml) will be passed in the `beforeStart()` phase.

The `pom.xml` for your adapter project will look similar to:

```
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.mycompany</groupId>
    <artifactId>mycompany-rre-adapter</artifactId>
    <version>1.1-SNAPSHOT</version>

    <properties>
        <jdk.version>1.8</jdk.version>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
        <rre.version>1.1</rre.version>
    </properties>

    <repositories>
        <repository>
            <id>sease</id>
            <name>Sease repository</name>
            <url>https://raw.github.com/SeaseLtd/rated-ranking-evaluator/mvn-repo</url>
        </repository>
    </repositories>

    <dependencies>
        <dependency>
            <groupId>io.sease</groupId>
            <artifactId>rre-search-platform-api</artifactId>
            <version>${rre.version}</version>
        </dependency>

        <!-- Other required libraries for interacting with your search engine API -->
    </dependencies>

</project>
```
