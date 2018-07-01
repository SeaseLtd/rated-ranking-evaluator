(function () {
    angular.module('myApp').factory('ConfigService', ConfigService);

    ConfigService.$inject = ['$log'];

    function ConfigService($log, $http) {

        /**
         * Request interval in milliseconds
         * @type {number}
         */
        var requestInterval = 5000;

        /**
         * The data request URL
         * @type {string}
         */
        var requestUrl = "http://127.0.0.1:8080/evaluation";

        init();

        return {
            requestInterval: requestInterval,
            requestUrl: requestUrl
        };

        ////////////

        /**
         * Init
         */
        function init() {
            $log.log("ConfigService", "starting");
        }

    }
})();
