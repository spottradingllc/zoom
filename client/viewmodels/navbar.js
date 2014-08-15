define(['plugins/router', 'durandal/app', 'jquery', 'knockout', 'service', 'model/loginModel', 'bootstrap' ], function (router, app, $, ko, service, login ) {


    return {
        router: router,
        login: login,
        isFAQ: function(title){
                if(title.search("FAQ") != -1){
                    return true;
                }
                else{
                    return false;
                }
            },
        activate: function () {
            router.map([
                //If you want to add a route, make sure to update the indices in navbar.html...
                { route: '', title: "Application State", moduleId: 'viewmodels/application_state', nav: true },
                { route: 'config', title: "Server Config", moduleId: 'viewmodels/server_config', nav: true },
                { route: 'appFAQ', title: "App State FAQ", moduleId: 'viewmodels/faq/application_state', nav: true },
                { route: 'configFAQ', title: "Server Config FAQ", moduleId: 'viewmodels/faq/server_config', nav: true }
            ]).buildNavigationModel();
            
            return router.activate();
        }
    };
});
