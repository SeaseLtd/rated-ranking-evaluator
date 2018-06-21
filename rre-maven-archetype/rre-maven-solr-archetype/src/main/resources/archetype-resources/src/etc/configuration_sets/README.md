This folder contains one subfolder for each configuration version. 
Each version folder should be a Solr home, so it should contain

* a solr.xml (even empty)
* one directory for each core containing a "conf" subfolder with all required files (e.g. schema.xml, solrconfig.xml)

This is an example:

* configuration_sets  
  * v1.0
    * core1
        * conf
            * schema.xml
            * solrconfig.xml
            * en_synonyms.txt
            * en_stopwords.txt    
    * core2
        * conf
            * schema.xml
            * solrconfig.xml
            * en_keywords.txt
  * solr.xml