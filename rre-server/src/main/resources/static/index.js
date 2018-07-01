var myApp = angular.module("myApp", ["ngRoute"])
    .run(function ($rootScope, $timeout) {

    });


myApp.config(function ($routeProvider) {
    $routeProvider
        .when("/", {
            templateUrl: "modules/main/views/dashboard.html",
            controller: "DashboardController"
        })
        .when("/dashboard", {
            templateUrl: "modules/main/views/dashboard.html",
            controller: "DashboardController"
        })
        .otherwise({
            template: "<h1>Not found</h1>"
        });
});