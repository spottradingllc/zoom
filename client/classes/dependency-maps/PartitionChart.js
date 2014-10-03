define([], function() {
    return function PartitionChart(d3, ko, parent, divName) {

        var self = this;
        self.parent = parent;

        self.name = 'Partition Chart';
        self.shortName = 'chart';

        self.root = null;
        self.g = null;
        self.currentlySelected = null;

        // visual parameters
        self.w = 1200;
        self.h = 1000;
        self.x = d3.scale.linear().range([0, self.w]);
        self.y = d3.scale.linear().range([0, self.h]);

        // create the initial visual and layout
        self.vis = d3.select('#d3-view-area').attr('class', 'chart')
            .style('width', self.w + 'px')
            .append('svg')
            .attr('width', self.w)
            .attr('display', 'none')
            .attr('id', self.shortName)
            .attr('height', self.h);

        self.partition = d3.layout.partition()
            .value(function(d) {
                return d.size;
            });

        // placeholders
        self.kx = null;
        self.ky = null;

        self.duration = 400;

        self.visible = ko.observable(false);

        self.show = function() {
            d3.select('#' + self.shortName).attr('display', 'inline');
            self.visible(true);
        };

        self.hide = function() {
            d3.select('#' + self.shortName).attr('display', 'none');
            self.visible(false);
        };

        self.inputJSON = function(json) {
            self.root = json;
            self.update(self.root);
        };

        self.update = function(source) {
            // setup for update
            self.vis.selectAll('g').remove();

            d3.select('#' + self.shortName).transition()
                .duration(self.duration)
                .attr('height', self.h);

            // join
            self.g = self.vis.selectAll('g')
                .data(self.partition.nodes(source));

            self.kx = self.w / source.dx;
            self.ky = self.h;

            // enter
            var gEnter = self.g.enter().append('svg:g')
                .attr('transform', function(d) {
                    return 'translate(' + self.x(d.y) + ',' + self.y(d.x) + ')';
                })
                .on('click', self.click);

            gEnter.append('svg:rect')
                .attr('width', source.dy * self.kx)
                .attr('fill', self.color)
                .attr('height', function(d) {
                    return d.dx * self.ky;
                })
                .attr('class', function(d) {
                    return d.children ? 'parent' : 'child';
                });

            gEnter.append('svg:text')
                .attr('transform', self.transform)
                .attr('dy', '.35em')
                .style('opacity', function(d) {
                    return d.dx * self.ky > 12 ? 1 : 0;
                })
                .text(function(d) {
                    return d.name;
                });

            gEnter.transition()
                .duration(self.duration)
                .attr('transform', function(d) {
                    return 'translate(' + self.x(d.y) + ',' + self.y(d.x) + ')';
                })
                .style('opacity', 1)
                .select('rect')
                .style('fill', self.color);

            // exit
            self.g.exit().transition()
                .duration(self.duration)
                .attr('transform', function(d) {
                    return 'translate(' + source.y + ',' + source.x + ')';
                })
                .style('opacity', 1e-6)
                .remove();

            // if some node was clicked, snap to it
            if (self.currentlySelected) {
                self.jumpInstantly(self.currentlySelected);
            }
        };

        self.click = function(d) {
            if (!d.children) {
                return;
            }

            self.currentlySelected = d;

            self.kx = (d.y ? self.w - 40 : self.w) / (1 - d.y);
            self.ky = self.h / d.dx;

            self.x.domain([d.y, 1]).range([d.y ? 40 : 0, self.w]);
            self.y.domain([d.x, d.x + d.dx]);

            var t = self.g.transition()
                .duration(d3.event.altKey ? 7500 : 750)
                .attr('transform', function(d) {
                    return 'translate(' + self.x(d.y) + ',' + self.y(d.x) + ')';
                });

            t.select('rect')
                .attr('width', d.dy * self.kx)
                .attr('height', function(d) {
                    return d.dx * self.ky;
                });

            t.select('text')
                .attr('transform', self.transform)
                .style('opacity', function(d) {
                    return d.dx * self.ky > 12 ? 1 : 0;
                });

            d3.event.stopPropagation();
        };

        self.jumpInstantly = function(d) {
            if (!d.children) {
                return;
            }

            self.kx = (d.y ? self.w - 40 : self.w) / (1 - d.y);
            self.ky = self.h / d.dx;

            self.x.domain([d.y, 1]).range([d.y ? 40 : 0, self.w]);
            self.y.domain([d.x, d.x + d.dx]);

            // no duration transition to a particular node
            var t = self.g.transition()
                .duration(0)
                .attr('transform', function(d) {
                    return 'translate(' + self.x(d.y) + ',' + self.y(d.x) + ')';
                });

            t.select('rect')
                .attr('width', d.dy * self.kx)
                .attr('height', function(d) {
                    return d.dx * self.ky;
                });

            t.select('text')
                .attr('transform', self.transform)
                .style('opacity', function(d) {
                    return d.dx * self.ky > 12 ? 1 : 0;
                });
        };

        // assign colors to nodes based on their status and whether or not they have children
        self.color = function(d) {
            if (d.status === 'running') {
                return parent.colors.green;
            }
            else if ((d.children || d._children) && d.status !== 'running') {
                return parent.colors.red;
            }
            else {
                return parent.colors.yellow;
            }
        };

        self.transform = function(d) {
            return 'translate(8,' + d.dx * self.ky / 2 + ')';
        };
    };
});
