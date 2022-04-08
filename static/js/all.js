import * as _ from '../vendor/underscore/js/underscore.esm.min.js'
import $ from '../vendor/jquery/js/jquery.esm.js'

$(function(){
    console.log('jQuery ready')
    console.log('Underscore.now()', _.now())

    $('[data-show-when-checked]').each(function(){
        var $el = $(this)
        var $checkbox = $('#' + $el.attr('data-show-when-checked'))
        var name = $checkbox.attr('name')

        var updateUI = function(){
            $el.toggleClass('d-none', ! $checkbox.is(':checked') )
        }

        $checkbox.on('change', updateUI)

        if ( name && $('input[name="' + name + '"]').length ) {
            $('input[name="' + name + '"]').on('change', updateUI)
        }

        updateUI()
    })
})
