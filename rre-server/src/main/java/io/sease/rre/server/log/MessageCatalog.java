package io.sease.rre.server.log;

/**
 * Search API log messages enumeration.
 * 
 * @author agazzarini
 * @since 1.0
 */
public interface MessageCatalog {
	String APPLICATION_NAME = "SEARCH-API";

	String _100001_DATA_ACCESS_FAILURE  = "<"+APPLICATION_NAME+"-100001> : Data Access Failure. Please check the log in order to see what happened.";
	String _100024_SEARCH_ENGINE_INTERNAL_FAILURE ="<"+APPLICATION_NAME+"-100024> : Search Engine Internal Failure. Please check the log in order to see what happened.";
	String _100025_UNABLE_TO_DETERMINE_POLICY ="<"+APPLICATION_NAME+"-100025> : Rules Engine was unable to determine the default policy that have to be associated with document id %s. As consequence of that it won't have any policy associated.";
	String _100026_POLICY_NOT_FOUND ="<"+APPLICATION_NAME+"-100026> : Rules Engine was unable to find a policy associated with the %s as name for document id %s. As consequence of that it won't have any policy associated.";
}