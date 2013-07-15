$(function() {

    $('select[name=pool]').on('change', function() {
        $('select[name=boot_image]').load('/pools/' + this.value.replace('/', '_') + '/images');
    });

});
