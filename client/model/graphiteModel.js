define(['jquery', 'model/constants'], function($, constants) {
    return function GraphiteModel(environment, host, configPath, platform) {
        var self = this;

        self.modalShow = function(urls) {
            $('#graphiteBody').empty();

            for (var i = 0; i < urls.length; ++i) {
                var url = urls[i];
                var html = '<img style="-webkit-user-select: none" src="' + url + '"/>';
                $('#graphiteBody').append($.parseHTML(html));
            }

            $('#graphiteModal').modal('show');
        };

        self.applicationURL = function() {
            var url = 'http://graphite' + environment + '/render?';
            var appName = configPath.replace(constants.zkPaths.statePath, '');
            var dotname = appName.replace(/\//g, '.');
            url = url + 'target=alias(secondYAxis(Infrastructure.startup.' + dotname + '.result), "Last Exit Code")';
            url = url + '&target=alias(Infrastructure.startup.' + dotname + '.runtime, "Startup Time")';
            url = url + '&from=-7d';
            url = url + '&yMinRight=-2';
            url = url + '&yMaxRight=2';
            url = url + '&yStepRight=1';
            url = url + '&lineMode=staircase';
            url = url + '&width=850';
            url = url + '&height=500';
            url = url + '&vtitle=Startup Time (seconds)';
            url = url + '&vtitleRight=Exit Code (0 = Success)';
            url = url + '&title=' + appName;
            return encodeURI(url);
        }();

        self.baseURL = function() {
            // http://graphite.readthedocs.org/en/latest/render_api.html
            var url = 'http://graphite' + environment + '/render?';
            url = url + '&from=-7d';
            url = url + '&width=850';
            url = url + '&height=500';
            return (url);
        }();

        self.cpuURL = function() {
            var url = self.baseURL;
            if (platform === constants.platform.windows) {
                url = url + '&target=alias(' + host + '.cputotals.sys,"CPU Totals sys")';
                url = url + '&target=alias(' + host + '.cputotals.user,"CPU Totals user")';
            }
            else {
                url = url + '&target=alias(' + host + '.cpuload.avg1,"CPU avg1 Load")';
            }
            url = url + '&yRight=0';
            url = url + '&title=' + host + '\'s CPU';
            url = url + '&vtitle=Load';
            return encodeURI(url);
        }();

        self.memoryURL = function() {
            var url = self.baseURL;
            if (platform === constants.platform.windows) {
                url = url + '&target=alias(' + host + '.memory.available_bytes,"Available Mem in Bytes")';
            }
            else {
                url = url + '&target=alias(' + host + '.meminfo.tot, "Total Memory")';
                url = url + '&target=alias(' + host + '.meminfo.used, "Memory Usage")';
            }
            url = url + '&title=' + host + '\'s Memory';
            url = url + '&vtitle=Bytes';
            return encodeURI(url);
        }();

        self.networkURL = function() {
            var url = self.baseURL;
            url = url + '&target=' + host + '.nettotals.kbin.*';
            url = url + '&target=' + host + '.nettotals.kbout.*';
            url = url + '&title=' + host + '\'s Network Usage';
            url = url + '&vtitle=KB sent/recieved';
            return encodeURI(url);
        }();

        self.diskSpaceURL = function() {
            var url = self.baseURL;
            if (platform === constants.platform.windows) {
                url = url + '&target=alias(' + host + '.diskinfo.c.available_bytes,"Available disk in Bytes")';
            }
            else {
                url = url + '&target=' + host + '.diskinfo.opt.total_bytes';
                url = url + '&target=' + host + '.diskinfo.opt.used_bytes';
            }
            url = url + '&title=' + host + '\'s Disk Space';
            url = url + '&vtitle= Bytes of Disk Space';
            return encodeURI(url);
        }();

        self.bufferErrorsURL = function() {
            var url = self.baseURL;
            url = url + '&target=' + host + '.tcpinfo.udperrs';
            url = url + '&target=' + host + '.nicinfo.*.rx_hardware_errors';
            url = url + '&title=' + host + '\'s Buffer Errors';
            url = url + '&vtitle= Errors';
            return encodeURI(url);
        }();
    };
});
