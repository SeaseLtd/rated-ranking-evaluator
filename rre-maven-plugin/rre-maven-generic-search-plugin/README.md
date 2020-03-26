Generic Maven Search plugin
===============================

This search plugin allows the use of alternative search APIs than the
supplied Solr and Elasticsearch choices.


## Usage

An example pom.xml, excluding most RRE configuration, would look like:

```
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.mycompany</groupId>
    <artifactId>my-evaluation-project</artifactId>
    <version>1.0</version>
    <packaging>pom</packaging>

    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
    </properties>

    <build>
        <plugins>
            <plugin>
                <groupId>io.sease</groupId>
                <artifactId>rre-maven-generic-search-plugin</artifactId>
                <version>1.0</version>
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
