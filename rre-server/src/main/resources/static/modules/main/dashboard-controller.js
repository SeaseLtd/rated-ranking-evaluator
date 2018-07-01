(function () {
    angular.module('myApp').controller('DashboardController', DashboardController);

    DashboardController.$inject = ['$scope', '$http', '$log', 'DataService', '$interval', 'ConfigService'];

    function DashboardController($scope, $http, $log, DataService, $interval, ConfigService) {
        var vm = this;

        // Scope vars
        vm.data = null;
        vm.isDetailOpen = [];

        // Methods
        vm.getMetricsCount = getMetricsCount;

        activate();

        ////////////

        /**
         * controller activation
         */
        function activate() {
            DataService.getData().then(
                function (response) {
                    vm.data = response.data;
                },
                function (error) {
                    $log.error("DataService - Error while performing request:", response);
                }
            );
            $interval(function () {
                DataService.getData().then(
                    function (response) {
                        vm.data = response.data;
                    },
                    function (error) {
                        $log.error("DataService - Error while performing request:", error);
                    }
                );
            }, ConfigService.requestInterval);
            $scope.vm = vm;
            $log.log('DashboardController', 'starting');
        }


        function getMetricsCount() {
            if (vm.data != null) {
                return Object.keys(vm.data.metrics).length;
            }
            return 0;
        }


    }
})();