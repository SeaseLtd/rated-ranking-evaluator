This folder contains one subfolder for each configuration version. 
Each version folder should contain a solr-settings.json file with details of
how to connect to the appropriate Solr core.

This is an example:

* configuration_sets  
  * v1.0
    * solr-settings.json
  * v1.1
    * solr-settings.json

The solr-settings.json files may have the following properties:

- `baseUrls`: an array of Solr base URLs (eg. `[ "http://localhost:8983/solr", "http://localhost:7574/solr" ]`).
- `collectionName` [**REQUIRED**]: the name of the collection or core being evaluated.
- `zkHosts`: an array of Zookeeper hosts (eg. `[ "zk1:2181", "zk2:2181" ]`).
- `zkChroot`: the path to the root Zookeeper node containing Solr data, if running in a Chroot environment (eg. `"/solr"`).
Optional.
- `connectionTimeoutMillis`: the number of milliseconds to wait for a connection to be made to Solr. Optional.
- `socketTimeoutMillis`: the number of milliseconds to allow for a response from Solr. Optional.

**Either** the baseUrls **or** the zkHosts property must contain values. If both are empty,
the configuration will fail to load.