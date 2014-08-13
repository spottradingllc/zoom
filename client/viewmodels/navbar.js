define(['plugins/router', 'durandal/app', 'jquery', 'knockout', 'service', 'model/loginModel' ], function (router, app, $, ko, service, login ) {


    return {
        router: router,
        login: login,
        activate: function () {
            router.map([
                { route: '', title: "Application State", moduleId: 'viewmodels/application_state', nav: true },
                { route: 'config', title: "Server Config", moduleId: 'viewmodels/server_config', nav: true },
                { route: 'appFAQ', title: "Application State FAQ", moduleId: 'viewmodels/application_state_faq', nav: true },
                { route: 'configFAQ', title: "Server Config FAQ", moduleId: 'viewmodels/server_config_faq', nav: true }
            ]).buildNavigationModel();
            
            return router.activate();
        }
    };
});
