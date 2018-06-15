/**
 * This is a controller
 *
 */
(function () {
    angular.module('App').controller('FeatureController', FeatureController);

    FeatureController.$inject = ['$scope', 'logger', 'resolvedValue'];
    function FeatureController($scope, logger, resolvedValue) {
        var vm = this;

        // Scope vars
        vm.variable = 'value';

        // Methods
        vm.aMethod = aMethod;


        activate();


        ////////////

        /**
         * controller activation
         */
        function activate() {
            logger.log('FeatureController', 'starting');
            vm.variable = resolvedValue.data;
        }


        /**
         * This is a method
         * @param param
         */
        function aMethod(param) {
            vm.variable = param;
        }


        /**
         * Watch a variable with $watch
         */
        $scope.$watch('vm.variable', watchVariable);
        function watchVariable(newValue) {
            logger.log('FeatureController', 'variable=' + newValue);
        }

    }
})();




/**
 *  This is a service, preferably it should be stateless but it's not mandatory
 *
 */
(function () {
    angular.module('App').factory('SimpleService', SimpleService);

    SimpleService.$inject = ['logger'];
    function SimpleService(logger) {

        var aVar; // A variable internal to the service

        init();

        return {
            aMethod: aMethod,
            anotherMethod: anotherMethod
        };



        ////////////

        /**
         * Init
         */
        function init(){

        }

        /**
         * A simple method
         */
        function aMethod(v) {
            aVar = v;
        }


        /**
         * Another simple method
         */
        function anotherMethod() {
            return aVar;
        }



    }


})();


/**
 *
 *  This shared model is used among various collaborating controllers to share data
 *  It's a lightweight object useful to hold shareable data
 *
 */
(function () {
    angular.module('App').service('sharedModel', sharedModel);

    sharedModel.$inject = [];
    function sharedModel() {
        var _this = this;

        // Properties
        _this.aVar = null;
        _this.anotherVar = '';

    }

})();



/**
 * This is a router config
 *
 */
(function () {

    angular.module('App').config(config);

    config.$inject = ['$routeProvider'];
    function config($routeProvider) {
        $routeProvider.when('/path/:id', {
            controller: 'FeatureController',
            controllerAs: 'vm',
            templateUrl: 'views/theview.html',
            resolve: {
                resolvedValue: ['$route', 'AService', function ($route, AService) {
                    return AService.get($route.current.params.id);
                }]
            }
        });
    }
})();


/**
 * This is a typical server-side API HTTP invocation.
 * Please notice the function returns the promise object coming from $http service invocation.
 * We prefer letting callers decide what to do with the promise.
 *
 * Ideally, this should be better placed in a service, as controllers and directives should not perform API calls directly.
 * @param params A JSON object representing the parameters to send
 * @returns {HttpPromise}
 */
function apiCallExample(params) {
    return $http({
        method: 'GET', // Or POST, PUT, DELETE, etc.
        url: theUrl,
        data: params
    });
}
