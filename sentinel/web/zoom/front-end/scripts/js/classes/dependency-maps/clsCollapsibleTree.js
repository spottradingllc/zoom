function CollapsibleTree(d3, ko, parent, divName) {
	// setup parent-child structure
	var self = this;
	self.parent = parent; 

	self.name = "collapsible-dependency-tree";

	// set visual parameters
	self.margin = {top: 20, right: 120, bottom: 20, left: 120};
	self.width = 5000 - self.margin.right - self.margin.left;
	self.height = 5000 - self.margin.top - self.margin.bottom;

	// setup tree
	self.i = 0;
	self.duration = 750;
	self.root = null;

	self.tree = d3.layout.tree()
						 .separation(function() {return 100;})
				         .size([self.height,self.width]);

	self.diagonal = d3.svg.diagonal()
    				  .projection(function(d) { return [d.y, d.x]; });

    // create SVG and bind it to the div
    self.svg = d3.select("#d3-view-area").append("svg")
										    .attr("width", self.width + self.margin.right + self.margin.left)
										    .attr("height", self.height + self.margin.top + self.margin.bottom)
										    .append("g")
										    .call(d3.behavior.zoom().scaleExtent([1, 8]).on("zoom", self.zoom))
										    .append("g")
										    .style("visibility", "hidden")
										    .attr("transform", "translate(" + self.margin.left + "," + self.margin.top + ")");

	self.inputJSON = function(json) {
		self.root = json;
		self.root.x0 = self.height/2;
		self.root.y0 = 0;
		self.update(self.root);
		
		self.root.children.forEach(self.collapse);
		self.update(self.root);
	}

	self.visible = ko.observable(false);

	self.hide = function() {
		self.svg.style("visibility", "hidden");
		self.visible(false);
	}

	self.show = function() {
		self.svg.style("visibility", "visible");
		self.visible(true);
	}

	self.collapse = function(d) {
		if (d.children) {
			d._children = d.children;
			d._children.forEach(self.collapse);
			d.children = null;
		}
	}

	self.zoom = function() {
		self.svg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
	}

	//d3.select(self.frameElement).style("height", "1200px");

	self.update = function(source) {
		var nodes = self.tree.nodes(self.root);
		var links = self.tree.links(nodes);

		nodes.forEach(function(d) { d.y = d.depth * 180});

		var node = self.svg.selectAll("g.node")
					  .data(nodes, function(d) {return d.id || (d.id = ++self.i)});

		// Enter any new nodes at the parent's previous position.
		var nodeEnter = node.enter().append("g")
									.attr("class", "node")
									.attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"})
									.on("click", self.click);

		nodeEnter.append("circle")
			     .attr("r", 1e-6)
			     .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });

		nodeEnter.append("text")
				 .attr("x", function(d) { return d.children || d._children ? -10 : 10; })
				 .attr("dy", ".35em")
				 .attr("text-anchor", function(d) { return d.children || d._children ? "end" : "start"; })
				 .text(function(d) { return d.name; })
				 .style("fill-opacity", 1e-6);

		// Transition nodes to their new position.
		var nodeUpdate = node.transition()
      						 .duration(self.duration)
      						 .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });


 		nodeUpdate.select("circle")
		 		  .attr("r", function(d) {return (d.size + 1)/10})
		 		  .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });

 		nodeUpdate.select("text")
 		    	  .style("fill-opacity", 1);

 		// Transition exiting nodes to the parent's new position.
 		var nodeExit = node.exit().transition()
 						   		  .duration(self.duration)
 						   		  .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
 						   		  .remove();

 		nodeExit.select("circle")
 		        .attr("r", 1e-6);

 		nodeExit.select("text")
 		        .style("fill-opacity", 1e-6);

 		// Update the links…
 		var link = self.svg.selectAll("path.link")
 		              .data(links, function(d) { return d.target.id; });

 		// Enter any new links at the parent's previous position.
 		link.enter().insert("path", "g")
 		    		.attr("class", "link")
 		    		.attr("d", function(d) {
 		      			var o = {x: source.x0, y: source.y0};
 		      			return self.diagonal({source: o, target: o});
 		    		});

 		// Transition links to their new position.
 		link.transition()
 		    .duration(self.duration)
 		    .attr("d", self.diagonal);

 		// Transition exiting nodes to the parent's new position.
 		link.exit().transition()
 		    	   .duration(self.duration)
		 		   .attr("d", function(d) {
	 		       		var o = {x: source.x, y: source.y};
	 		        	return self.diagonal({source: o, target: o});
	 		    	})
		 		    .remove();

 		// Stash the old positions for transition.
 		nodes.forEach(function(d) {
 		  d.x0 = d.x;
 		  d.y0 = d.y;
 		});
	}

	self.click = function(d) {
		if (d.children) {
			d._children = d.children;
			d.children = null;
		} 
		else {
			d.children = d._children;
			d._children = null;
		}
		self.update(d);
	}
}