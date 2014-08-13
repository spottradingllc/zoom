define(['plugins/router', 'durandal/app', 'jquery', 'knockout', 'service', 'model/loginModel' ], function (router, app, $, ko, service, login ) {


    return {
        router: router,
        login: login,
        activate: function () {
            router.map([
                { route: '', title: "Application State", moduleId: 'viewmodels/application_state', nav: true },
                { route: 'config', title: "Server Config", moduleId: 'viewmodels/server_config', nav: true }
            ]).buildNavigationModel();
            
            return router.activate();
        }
    };
});
