(function () {
    angular.module('myApp').factory('DataService', DataService);

    DataService.$inject = ['$log', '$http', 'ConfigService'];

    function DataService($log, $http, ConfigService) {

        init();

        return {
            getData: getData
        };

        ////////////

        /**
         * Init
         */
        function init() {
            $log.log("DataService", "starting");
        }

        function getData() {
            return $http.get(ConfigService.requestUrl);
        }
    }
})();
