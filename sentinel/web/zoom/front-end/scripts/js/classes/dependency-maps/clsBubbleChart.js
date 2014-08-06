function BubbleChart(d3, ko, parent, divName) {

	var self = this;
	self.parent = parent;

	self.w = 1200;
	self.h = 800;
	self.r = 720;
	self.x = d3.scale.linear().range([0, self.r]);
	self.y = d3.scale.linear().range([0, self.r]);

	self.name = "bubble-chart";

	self.node = null;
	self.root = null;

	self.visible = ko.observable(false);

	self.pack = d3.layout.pack()
				  .size([self.r, self.r])
				  .value(function(d) { return d.size/self.r; })

	self.vis = d3.select("#d3-view-area").insert("svg:svg", "h2")
									     .attr("width", self.w)
									     .attr("height", self.h)
									     .attr("id", self.name)
									     .style("display", "none")
									     .append("svg:g")
									     .attr("transform", "translate(" + (self.w - self.r) / 2 + "," + (self.h - self.r) / 2 + ")");

	self.show = function() {
		var json = self.parent.dependents();

		self.node = self.root = json;

		var nodes = self.pack.nodes(self.root);

		self.vis.selectAll("circle")
		    .data(nodes)
		    .enter().append("svg:circle")
		    .attr("class", function(d) { return d.children ? "parent" : "child"; })
		    .attr("cx", function(d) { return d.x; })
		    .attr("cy", function(d) { return d.y; })
		    .attr("r", function(d) { return d.r; })
		    .attr("fill", function(d) {return self.color(d);})
		    .on("click", function(d) { return self.zoom(self.node == d ? self.root : d); });

		self.vis.selectAll("circle")
				.append("svg:title")
				.text(function(d){return d.name;});

		self.vis.selectAll("text")
		    .data(nodes)
		    .enter().append("svg:text")
		    .attr("class", function(d) { return d.children ? "parent" : "child"; })
		    .attr("x", function(d) { return d.x; })
		    .attr("y", function(d) { return d.y; })
		    .attr("dy", ".35em")
		    .attr("text-anchor", "middle")
		    .style("opacity", function(d) { return d.r > 20 ? 1 : 0; })
		    .text(function(d) { if(!d.children) return d.name; });

		d3.select(window).on("click", function() { self.zoom(self.root); });

		d3.select("#" + self.name).style("display", "inline");
		self.visible(true);
	}

	self.hide = function() {
		d3.select("#" + self.name).style("display", "none");
		self.visible(false);
	}

	self.zoom = function(d, i) {
		var k = self.r / d.r / 2;
		self.x.domain([d.x - d.r, d.x + d.r]);
		self.y.domain([d.y - d.r, d.y + d.r]);

		var t = self.vis.transition()
		    .duration(d3.event.altKey ? 7500 : 750);

		t.selectAll("circle")
		    .attr("cx", function(d) { return self.x(d.x); })
		    .attr("cy", function(d) { return self.y(d.y); })
		    .attr("r", function(d) { return k * d.r; });

		t.selectAll("text")
		    .attr("x", function(d) { return self.x(d.x); })
		    .attr("y", function(d) { return self.y(d.y); })
		    .style("opacity", function(d) { return k * d.r > 20 ? 1 : 0; });

		self.node = d;
		d3.event.stopPropagation();
	}

	// assign colors to nodes based on their status and whether or not they have children
	self.color = function(d) {
	    if (d.status == "running") {
	        return parent.colors.green;
	    }
	    else if (!d.children && d.status != "running") {
	        return parent.colors.yellow;
	    }
	    else {
	        return parent.colors.red;
	    }
	}
}