$(function() {

    var generateImageUploadURL = function() {
        $('#url_generator_target').html(
            $('#url_generator_zygote').html()
                                      .replace('__VERSION__', $('.url_generator.version').val())
                                      .replace('__KERNEL__', $('.url_generator.kernel').val())
        );

    };

    $('select.url_generator').on('change', generateImageUploadURL);
    $('input.url_generator').on('keyup', generateImageUploadURL);


    $('#farm_graph').each(function() {

        var sigInst = sigma.init(this).drawingProperties({
                                            defaultLabelColor: '#fff',
                                       })

                                      .graphProperties({
                                            minNodeSize: 0.5,
                                            maxNodeSize: 5,
                                       });












        sigInst.bind('overnodes',function(event){

            var nodes = event.content;
            var neighbors = {};

            sigInst.iterEdges(function(e) {
                if(nodes.indexOf(e.source)>=0 || nodes.indexOf(e.target)>=0) {
                    neighbors[e.source] = 1;
                    neighbors[e.target] = 1;
                }

            }).iterNodes(function(n) {

              if(!neighbors[n.id])
                n.hidden = 1;
              else
                n.hidden = 0;

            }).draw(2,2,2);

          }).bind('outnodes',function() {

            sigInst.iterEdges(function(e) {

              e.hidden = 0;

            }).iterNodes(function(n){

              n.hidden = 0;

            }).draw(2,2,2);

          });

        sigInst.parseGexf('/farms?gexf=');

        sigInst.draw();

    });

});
