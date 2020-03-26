Generic Maven RRE Search plugin
===============================

This archetype provides the basic setup necessary to connect RRE to a generic
search API. Unlike the other archetypes, this requires more configuration in
its pom.xml. In particular, you **must** set the following configuration
properties:

- a dependency in the rre-maven-generic-search-plugin that refers to the
implementation of SearchPlatform you intend to use.
- `searchPlatform` in the configuration options must contain the name of
the search platform implementation class to be used.
- `searchPlatformConfiguration` may be used to pass an optional set of
configuration dependencies into the SearchPlatform.

The supplied pom.xml file contains placeholders for this configuration.

In addition, you are likely to need to change the configuration settings
files to contain the relevant information to communicate with your
search API.


## Implementing SearchPlatform

To supply your own search platform, you need to implement the 
[SearchPlatform](https://github.com/SeaseLtd/rated-ranking-evaluator/blob/master/rre-search-platform/rre-search-platform-api/src/main/java/io/sease/rre/search/api/SearchPlatform.java)
interface, which provides the connection between RRE and your search engine.
Your implementation should have a zero-argument constructor - the 
configuration properties (set in the `searchPlatformConfiguration` block
in your pom.xml) will be passed in the `beforeStart()` phase.
 