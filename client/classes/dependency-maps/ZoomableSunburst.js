function ZoomableSunburst(d3, ko, parent, divName) {
	// setup parent-child structure
	var self = this;
	self.parent = parent; 

	self.root = null;
	self.name = "zoomable-sunburst";

	self.width = 800;
	self.height = 800;
	self.radius = Math.min(self.width, self.height) / 2;

	self.svg = d3.select("#d3-view-area").append("svg")
	            			   			 .attr("width", self.width)
	    					   			 .attr("height", self.height)
	    					   			 .attr("id", self.name)
	    					   			 .style("display", "none")
	    					   			 .append("g")
	    					   			 .attr("transform", "translate(" + self.width / 2 + "," + (self.height / 2 + 10) + ")");

	self.x = d3.scale.linear()
    		         .range([0, 2 * Math.PI]);

    self.y = d3.scale.sqrt()
    			.range([0, self.radius]);

    self.color = d3.scale.category20c();

    self.inputJSON = function(json) {
    	self.root = json;
    	self.root.x0 = 0;
    	self.root.y0 = 0;
    	self.update(self.root);
    }

    self.visible = ko.observable(false);

    self.hide = function() {
    	d3.select("#" + self.name).style("display", "none");
    	self.visible(false);
    }

    self.show = function() {
    	d3.select("#" + self.name).style("display", "inline");
    	self.visible(true);
    }

    self.update = function(source) {
    	self.svg.selectAll("path").remove();

	    self.partition = d3.layout.partition()
	    				          .value(function(d) { return d.size; });

	    self.arc = d3.svg.arc()
	    				 .startAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, self.x(d.x))); })
	    				 .endAngle(function(d) { return Math.max(0, Math.min(2 * Math.PI, self.x(d.x + d.dx))); })
	    				 .innerRadius(function(d) { return Math.max(0, self.y(d.y)); })
	    				 .outerRadius(function(d) { return Math.max(0, self.y(d.y + d.dy)); });

	    self.path = self.svg.selectAll("path")
				       .data(self.partition.nodes(source))
				       .enter().append("path")
				       .attr("d", self.arc)
				       .style("fill", function(d) { return self.color((d.children ? d : d.parent).name); })
				       .on("click", self.click)
				       .each(function(d) {
				           this.x0 = d.x;
				           this.dx0 = d.dx;
				        });

		self.g = self.svg.selectAll("g")
						 .data(self.partition.nodes(self.root))
						 .enter().append("g");


	}

	self.computeRotation = function(d) {
		var angle = self.x(d.x + d.dx /2) - Math.PI/2;
		return (angle/Math.PI * 180);
	}

	self.click = function(d) {
		self.path.transition()
				 .duration(750)
				 .attrTween("d", self.arcTween(d))
	}

	self.arcTween = function(d) {
		var xd = d3.interpolate(self.x.domain(), [d.x, d.x + d.dx]);
		var yd = d3.interpolate(self.y.domain(), [d.y, 1]);
		var yr = d3.interpolate(self.y.range(), [d.y ? 20 : 0, self.radius]);

		return function(d, i) {
			return i ? function(t) {return self.arc(d);} : function(t) {
															self.x.domain(xd(t)); 
															self.y.domain(yd(t)).range(yr(t)); 
															return self.arc(d); 
														};
		}
	}

	self.arcTweenUpdate = function(a) {
		var i = d3.interpolate({x: this.x0, dx: this.dx0}, a);
		return function(t) {
		    var b = i(t);
		    this.x0 = b.x;
		    this.dx0 = b.dx;
		    return self.arc(b);
		};
	}
}