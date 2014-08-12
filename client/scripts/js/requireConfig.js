require.config({
    // By default, load any module IDs from front-end/scripts/js ...
    baseUrl: 'front-end/scripts/js',

    // ...Except if the module ID is a 3rd-party library, then load it
    // from the front-end/scripts/js/lib directory.
    //
    // Path configuration is relative to "baseUrl", and never includes
    // a ".js" extension since paths configuration could be for a directory.
    paths: {
        libs: './libs',
        jquery: './libs/jquery-2.1.1.min',
        knockout: './libs/knockout-3.1.0',
        bootstrap: './libs/bootstrap.min',
        sammy: './libs/sammy-0.7.4.min',
        d3: './libs/d3'
    }
});
