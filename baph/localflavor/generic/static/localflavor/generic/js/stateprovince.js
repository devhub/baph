/**
 * @preserve
 * Handles associating the proper states/provinces with the selected country,
 * if any exist in the list.
 * @author Mark Lee <markl@evomediagroup.com>
 */
jQuery(function () {
    function get_country_class(country) {
        var ccode;
        ccode = jQuery('option:selected', country).val().toLowerCase();
        return 'country-' + ccode;
    }
    jQuery('.localflavor-generic-country').each(function () {
        var country, jcountry;
        country = this;
        jcountry = jQuery(this);
        jcountry.ready(function () {
            var cls, cdict, form, state, sparent;
            cls = get_country_class(country);
            cdict = {};
            form = jcountry.parents('form');
            state = jQuery('.localflavor-generic-stateprovince');
            state.children('option').each(function () {
                var jopt, opt_cls;
                jopt = jQuery(this);
                opt_cls = jopt.attr('class');
                if (!cdict[opt_cls]) {
                    cdict[opt_cls] = [];
                }
                cdict[opt_cls].push(this);
                if (!jopt.hasClass(cls)) {
                    jopt.remove();
                }
            }); // $(option).each()
            state.data('per_country', cdict);
            if (state.children('option').length == 0) {
                state.parents('tr, p').hide();
            }
        }); // jcountry.ready()
        jcountry.change(function () {
            var cls, form, state, sparent, states;
            cls = get_country_class(country);
            form = jcountry.parents('form');
            state = jQuery('.localflavor-generic-stateprovince');
            sparent = state.parents('tr, p');
            state.children('option').remove();
            states = state.data('per_country')[cls];
            if (states) {
                jQuery.each(states, function () {
                    state.append(this);
                });
                state.children('option:first').attr('selected', 'selected');
                sparent.show()
            } else {
                sparent.hide();
            }
        }); // jcountry.change()
    }); // $(.country).each()
}); // $.ready()
