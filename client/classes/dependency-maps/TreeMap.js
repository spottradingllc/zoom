function TreeMap(d3, ko, parent, divName) {

    var self = this;
    self.parent = parent;

    self.w = 1280 - 80;
    self.h = 800 - 180;
    self.x = d3.scale.linear().range([0, self.w]);
    self.y = d3.scale.linear().range([0, self.h]);
    self.color = d3.scale.category20c();
    self.root = null;
    self.node = null;

    self.name = 'tree-map';

    self.partition = d3.layout.partition()
        .children(function(d) {
            return isNaN(d.value) ? d3.entries(d.value) : null;
        })
        .value(function(d) {
            return d.value;
        });

    self.svg = d3.select('body').append('svg')
        .attr('width', self.width)
        .attr('height', self.height);

    self.rect = self.svg.selectAll('rect');

    self.visible = ko.observable(false);

    self.show = function() {
        self.rect.data(self.partition(d3.entries(self.parent.dependents())[0]))
            .enter().append('rect')
            .attr('x', function(d) {
                return self.x(d.x);
            })
            .attr('y', function(d) {
                return self.y(d.y);
            })
            .attr('width', function(d) {
                return self.x(d.dx);
            })
            .attr('height', function(d) {
                return self.y(d.dy);
            })
            .attr('fill', function(d) {
                return self.color((d.children ? d : d.parent).key);
            })
            .on('click', self.clicked);
    };

    self.hide = function() {
        d3.select('#' + self.name).style('display', 'none');
        self.visible(false);
    };


    self.size = function(d) {
        return d.size;
    };

    self.clicked = function(d) {
        self.x.domain([d.x, d.x + d.dx]);
        self.y.domain([d.y, 1]).range([d.y ? 20 : 0, self.height]);

        self.rect.transition()
            .duration(750)
            .attr('x', function(d) {
                return self.x(d.x);
            })
            .attr('y', function(d) {
                return self.y(d.y);
            })
            .attr('width', function(d) {
                return self.x(d.x + d.dx) - self.x(d.x);
            })
            .attr('height', function(d) {
                return self.y(d.y + d.dy) - self.y(d.y);
            });
    };
}