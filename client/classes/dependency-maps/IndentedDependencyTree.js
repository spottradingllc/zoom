define([], function() {
    return function IndentedDependencyTree(d3, ko, parent, divName) {
        // setup parent-child structure
        var self = this;
        self.parent = parent;

        self.name = 'Indented Dependency Tree';
        self.shortName = 'tree';

        // set visual parameters
        self.margin = {top: 30, right: 20, bottom: 30, left: 20};
        self.width = 1200 - self.margin.left - self.margin.right;
        self.barHeight = 30;
        self.barWidth = self.width * 0.8;

        self.openedNodes = ko.observableArray([]);

        // setup tree
        self.i = 0;
        self.duration = 400;
        self.root = null;

        self.tree = d3.layout.tree()
            .nodeSize([0, 20]);

        self.diagonal = d3.svg.diagonal()
            .projection(function(d) {
                return [d.y, d.x];
            });

        // create SVG and bind it to the div
        self.svg = d3.select('#d3-view-area').append('svg')
            .attr('width', self.width + self.margin.left + self.margin.right)
            .attr('id', self.shortName)
            .style('display', 'none')
            .append('g')
            .style('margin-top', '0px')
            .attr('transform', 'translate(' + self.margin.left + ',' + self.margin.top + ')');

        self.inputJSON = function(json) {
            self.root = json;
            self.root.x0 = 0;
            self.root.y0 = 0;
            self.root.children.forEach(self.collapse);

            self.update(self.root);

            self.reOpenAllNodes();
        };

        self.visible = ko.observable(false);

        self.hide = function() {
            d3.select('#' + self.shortName).style('display', 'none');
            self.visible(false);
        };

        self.show = function() {
            d3.select('#' + self.shortName).style('display', 'block');
            self.visible(true);
        };

        self.update = function(source) {
            var nodes = self.tree.nodes(self.root);

            var height = nodes.length * self.barHeight + self.margin.top + self.margin.bottom;

            d3.select('svg').transition()
                .duration(self.duration)
                .attr('height', height);

            d3.select(self.frameElement).transition()
                .duration(self.duration)
                .style('height', height + 'px');

            nodes.forEach(function(n, i) {
                n.x = i * self.barHeight;
            });

            var node = self.svg.selectAll('g.node')
                .data(nodes, function(d) {
                    d.context = self.assignContext(d);
                    return d.id || (d.id = ++self.i);
                });

            var nodeEnter = node.enter().append('g')
                .attr('class', 'node')
                .attr('transform', function(d) {
                    return 'translate(' + source.y0 + ',' + source.x0 + ')';
                })
                .style('opacity', 1e-6);

            nodeEnter.append('rect')
                .attr('y', -self.barHeight / 2)
                .attr('height', self.barHeight)
                .attr('width', self.barWidth)
                .style('fill', self.color)
                .on('dblclick', self.openInTable)
                .attr('color', self.color);

            nodeEnter.append('text')
                .attr('dy', 3.5)
                .attr('dx', 5.5)
                .on('click', self.toggleExpansion)
                .text(function(d) {
                    return self.nodeName(d);
                });

            self.svg.selectAll('.node text')
                .text(function(d) {
                    return self.nodeName(d);
                });

            nodeEnter.append('svg:title')
                .text(function(d) {
                    return self.nodeTitle(d);
                });

            // Transition nodes to their new position.
            nodeEnter.transition()
                .duration(self.duration)
                .attr('transform', function(d) {
                    return 'translate(' + d.y + ',' + d.x + ')';
                })
                .style('opacity', 1);

            node.transition()
                .duration(self.duration)
                .attr('transform', function(d) {
                    return 'translate(' + d.y + ',' + d.x + ')';
                })
                .style('opacity', 1)
                .select('rect')
                .style('fill', self.color);

            // Transition exiting nodes to the parent's new position.
            node.exit().transition()
                .duration(self.duration)
                .attr('transform', function(d) {
                    return 'translate(' + source.y + ',' + source.x + ')';
                })
                .style('opacity', 1e-6)
                .remove();

            var link = self.svg.selectAll('path.link')
                .data(self.tree.links(nodes), function(d) {
                    return d.target.id;
                });

            // Enter any new links at the parent's previous position.
            link.enter().insert('path', 'g')
                .attr('class', 'link')
                .attr('d', function(d) {
                    var o = {x: source.x0, y: source.y0};
                    return self.diagonal({source: o, target: o});
                })
                .transition()
                .duration(self.duration)
                .attr('d', self.diagonal);

            // Transition links to their new position.
            link.transition()
                .duration(self.duration)
                .attr('d', self.diagonal);

            // Transition exiting nodes to the parent's new position.
            link.exit().transition()
                .duration(self.duration)
                .attr('d', function(d) {
                    var o = {x: source.x, y: source.y};
                    return self.diagonal({source: o, target: o});
                })
                .remove();

            // Stash the old positions for transition.
            nodes.forEach(function(d) {
                d.x0 = d.x;
                d.y0 = d.y;
            });
        };


        // Toggle children on click.
        self.toggleExpansion = function(d) {
            // expand/collapse children
            if (d.children) {
                if (self.openedNodes.indexOf(d.context) > -1) {
                    self.openedNodes.remove(d.context);
                }
                d._children = d.children;
                d.children = null;
            }
            else {
                if (self.openedNodes.indexOf(d.context) === -1) {
                    self.openedNodes.push(d.context);
                }
                d.children = d._children;
                d._children = null;
            }
            // properly update text label
            self.update(d);
        };

        self.openInTable = function(d) {
            // open child d in table
            self.parent.parent.filterBy(d.name);
            self.hide();
        };

        self.collapse = function(d) {
            if (d.children) {
                d._children = d.children;
                d._children.forEach(self.collapse);
                d.children = null;
            }
        };

        self.reOpenAllNodes = function() {
            if (!self.root || !self.root.children) {
                return;
            }
            self.root.children.forEach(function(d) {
                if (self.openedNodes.indexOf(d.context) > -1) {
                    self.toggleExpansion(d);

                    // call recursive helper on each of the node's children
                    if (d.children) {
                        d.children.forEach(function(child) {
                            self.reOpenChildrenAtNode(child);
                        });
                    }
                }
            });
        };

        self.reOpenChildrenAtNode = function(node) {
            if (self.openedNodes.indexOf(node.context) > -1) {
                self.toggleExpansion(node);
            }

            if (!node.children) {
                return;
            }
            else {
                node.children.forEach(function(child) {
                    self.reOpenChildrenAtNode(child);
                });
            }
        };

        self.assignContext = function(d) {
            var context = d.name;
            if (d.parent) {
                context += self.assignContext(d.parent);
            }
            else {
                return context;
            }

            return context;
        };

        // assign colors to nodes based on their status and the status of their children
        self.color = function(d) {
            if (d.status === 'running' && self.allChildrenUp(d)) {
                return parent.colors.green;
            }
            else if (d.status === 'running' && !self.allChildrenUp(d)) {
                return parent.colors.green;
            }
            else if (d.status !== 'running' && self.allChildrenUp(d)) {
                return parent.colors.yellow;
            }
            else {
                return parent.colors.red;
            }
        };

        // function to see if all of the children of a particular node are running
        self.allChildrenUp = function(d) {
            if (d._children) {
                for (var i = 0; i < d._children.length; i++) {
                    if (d._children[i].status === 'stopped') {
                        return false;
                    }
                }
            }
            else if (d.children) {
                for (var j = 0; j < d.children.length; j++) {
                    if (d.children[j].status === 'stopped') {
                        return false;
                    }
                }
            }
            else {
                return true;
            }
            return true;
        };

        // determine a node name based on expanded/collapsed/nonexistant children
        self.nodeName = function(d) {
            if (d._children) {
                return d.name + ' (' + d.errorState + ') +';
            }
            else if (d.children) {
                return d.name + ' (' + d.errorState + ') -';
            }
            else {
                return d.name + ' (' + d.errorState + ')';
            }
        };

        self.nodeTitle = function(d) {
            if (d.status === 'running' && self.allChildrenUp(d)) {
                return 'Up with all children up.';
            }
            else if (d.status === 'running' && !self.allChildrenUp(d)) {
                return 'Up with at least one child down.';
            }
            else if (d.status !== 'running' && self.allChildrenUp(d)) {
                return 'Down with all children up.';
            }
            else {
                return 'Down with at least one child down.';
            }
        };
    };
});
