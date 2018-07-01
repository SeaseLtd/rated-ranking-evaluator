(function () {
    angular.module('myApp').controller('NavbarController', NavbarController);

    NavbarController.$inject = ['$scope', '$http', '$log', 'DataService'];

    function NavbarController($scope, $http, $log, DataService) {
        var vm = this;

        // Scope vars
        activate();

        ////////////

        /**
         * controller activation
         */
        function activate() {
            $log.log('NavbarController', 'starting');
            DataService.getData().then(
                function (response) {
                    vm.navBarTitle = response.data.name;
                },
                function (error) {
                    $log.error("DataService - Error while performing request:", error);
                }
            );

            $scope.vm = vm;
        }

    }
})();