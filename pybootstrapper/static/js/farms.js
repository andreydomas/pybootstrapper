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

        sigInst.parseGexf('/farms?gexf=');

        sigInst.draw();

    });

});
