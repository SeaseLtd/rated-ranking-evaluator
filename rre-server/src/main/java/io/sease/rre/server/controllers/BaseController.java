package io.sease.rre.server.controllers;

/**
 * Supertype layer for all REST controllers.
 *
 * @author agazzarini
 * @since 1.0
 */
public abstract class BaseController {
   /* protected final Log logger = new Log(getClass());
    private final List<Rule> defaultRuleset = asList(Rule.DEFAULT_RULE);

    // TODO
    protected List<Rule> rules() {
        return defaultRuleset;
    }

    @ResponseStatus(value = HttpStatus.INTERNAL_SERVER_ERROR, reason = "Search Engine Subsystem internal failure has occurred.")
    @ExceptionHandler(SolrException.class)
    public void searchSystemFailure(final SolrException exception) {
        logger.error(MessageCatalog._100024_SEARCH_ENGINE_INTERNAL_FAILURE, exception);
    }

    @ResponseStatus(value = HttpStatus.INTERNAL_SERVER_ERROR, reason = "Data Subsystem internal failure has occurred.")
    @ExceptionHandler(DataAccessException.class)
    public void dataAccessFailure(final DataAccessException exception) {
        logger.error(MessageCatalog._100001_DATA_ACCESS_FAILURE, exception);
    }

    @ResponseStatus(value = HttpStatus.NOT_FOUND, reason = "Request resource doesn't exist.")
    @ExceptionHandler(ResourceNotFoundException.class)
    public void resourceDoesntExist(final ResourceNotFoundException exception) {
        logger.error(MessageCatalog._100001_DATA_ACCESS_FAILURE, exception);
    }*/
}