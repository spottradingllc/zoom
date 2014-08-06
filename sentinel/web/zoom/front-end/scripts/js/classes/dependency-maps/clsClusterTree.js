function ClusterTree(d3, ko, parent, divName) {
	var self = this;
	self.parent = parent;

	self.name = "cluster-tree";

	self.width = 7000;
	self.height = 20000;

	self.cluster = d3.layout.cluster()
				            .size([self.height, self.width - 160]);

	self.svg = d3.select("#d3-view-area").append("svg")
				                         .attr("width", self.width)
				                         .attr("height", self.height)
				                         .attr("id", self.name)
				                         .attr("display", "none")
				                         .append("g")
				                         .attr("transform", "translate(40,0)")

	self.visible = ko.observable(false);

	self.hide = function() {
		d3.select("#" + self.name).attr("display", "none");
		self.visible(false);
	}

	self.show = function() {
		d3.select("#" + self.name).attr("display", "inline");
		self.visible(true);
	}

	d3.json("test.json", function(json) {
		var nodes = self.cluster.nodes(json);

		var link = self.svg.selectAll("path.link")
				       .data(self.cluster.links(nodes))
				       .enter().append("path")
				       .attr("class", "link")
				       .attr("d", self.elbow)

		var node = self.svg.selectAll(".node")
						   .data(nodes)
						   .enter().append("g")
						   .attr("class", "node")
						   .attr("transform", function(d) {return "translate(" + d.y + "," + d.x + ")"; })

		node.append("circle")
			.attr("r", 4.5)

		node.append("text")
			.attr("dx", function(d) { return d.children ? -8 : 8; })
			      .attr("dy", 3)
			      .style("text-anchor", function(d) { return d.children ? "end" : "start"; })
			      .text(function(d) { return d.name; });

	});

	self.elbow = function(d, i) {
		return "M" + d.source.y + "," + d.source.x + "V" + d.target.x + "H" + d.target.y;
	}
}