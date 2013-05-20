/**
 * Javascript used for customised deform template functionality.
 * User: Casey Bajema
 * Date: 24/09/12
 * Time: 4:44 PM
 */

// Javascript for help icons/text
function toggleHelp(help_icon) {
    var help_text = $(help_icon.parentNode).find('.help_text');
    if (help_text.length <= 0) {
        help_text = $(help_icon.parentNode.parentNode).find('.help_text')
    }
    help_text.first().toggle(200);
    $(help_icon).toggleClass("current");

}

// Used as an onclick function for toggling a sequence/mapping schema
function toggleCollapse(fieldset, group) {
    var speed = 200;
    var collapsible_item = $(fieldset.parentNode).children('ul').first();

    if (collapsible_item.is(':hidden')) {
//        if (group != "None") {
//            $(".collapsible-" + group).find(".collapsible_items").slideUp(speed);
//            $(".collapsible-" + group).find(".collapse_icon").html('+');
//        }
        $(fieldset).children('.collapse_icon')[0].innerHTML = ('-');
        collapsible_item.slideDown(speed);
//        $(fieldset.parentNode).css("background-color", "transparent");
    } else {
        $(fieldset).children('.collapse_icon')[0].innerHTML = ('+');
        collapsible_item.slideUp(speed);
//        $(fieldset.parentNode).css("background-color", "#99FFFF");
    }
}

// Used as an onclick function for toggling a sequence/mapping schema
function collapseAll(group) {
    $('.collapsible-' + group).find('.collapsible_items').slideUp(200);
}

// Used as an onclick function for toggling a sequence/mapping schema
function expandAll(group) {
    $('.collapsible-' + group).find('.collapsible_items').slideDown(200);
}

// Helper function for escaping quotes in ColanderAlchemy attributes (eg. default text/placeholder).
function escapeQuotes(text) {
    var i = 0;
    var text_array = text.split("'");
    text = "";
    for (i; i < text_array.length - 1; i++) {
        text = text.concat(text_array[i], "\\'");
    }
    text = text.concat(text_array[text_array.length - 1]);

    var text_array = text.split('"');
    text = "";
    for (i; i < text_array.length - 1; i++) {
        text = text.concat(text_array[i], '\\"');
    }
    text = text.concat(text_array[text_array.length - 1]);

    return text;
}

// When the form is submitted, clear placeholder text before values are read (otherwise empty fields would be filled with placeholder values).
function submitClearsDefaultValues(oid, default_text) {
    var form = document.getElementById('deform');
    default_text = escapeQuotes(default_text);

    var submit_text = "if (document.getElementById('" + oid + "') != null && document.getElementById('" + oid + "').value == '" + default_text + "') {document.getElementById('" + oid + "').value = '';}";

    if (form.getAttribute('onsubmit') != null) {
        submit_text += form.getAttribute('onsubmit');
    }
    form.setAttribute('onsubmit', submit_text);
}

// Hide all descriptions on the current page
function hideDescriptions(hide) {
    document.hide_descriptions = hide;

    if (hide) {
        $(".description").addClass("hidden");
    } else {
        $(".description").removeClass("hidden");
    }
}


/*function fixHTMLTags(descText) {
 while (descText.match("\&lt;")) {
 descText = descText.replace("\&lt;", "<");
 }

 while (descText.match("\&gt;")) {
 descText = descText.replace("\&gt;", ">");
 }

 return descText;
 }

 $(document).ready(function () {

 });
 */


//--------------------------Map_sequence Template------------------------------------
// All features (points/polygons) are added to a map layer, find the layer the feature is on for the given map.
function findMapLayerFromFeature(feature, map) {
    var i = 0, j = 0, k = 0;
    if (typeof map === "undefined") {
        for (i; i < document.location_maps.length; i++) {
            for (j; j < document.location_maps[i].layers.length; j++) {
                if ((OpenLayers.Layer.Vector.prototype.isPrototypeOf(document.location_maps[i].layers[j]))) {
                    for (k; k < document.location_maps[i].layers[j].features.length; k++) {
                        if (document.location_maps[i].layers[j].features[k] == feature) {
                            return document.location_maps[i].layers[j];
                        }
                    }
                }
            }
        }
    } else {
        for (j; j < document.location_maps[i].layers.length; j++) {
            if ((OpenLayers.Layer.Vector.prototype.isPrototypeOf(document.location_maps[i].layers[j]))) {
                for (k; k < document.location_maps[i].layers[j].features.length; k++) {
                    if (document.location_maps[i].layers[j].features[k] == feature) {
                        return document.location_maps[i].layers[j];
                    }
                }
            }
        }
    }

    return null;
}

// Find the map that the provided layer is on.
function findMapFromLayer(layer) {
    var i = 0, j = 0, k = 0;
    for (i; i < document.location_maps.length; i++) {
        for (j; j < document.location_maps[i].layers.length; j++) {
            if (document.location_maps[i].layers[j] == layer) {
                return document.location_maps[i];
            }
        }
    }
    return null;
}

// Add a location to the map sequence (this is the empty boxes below the displayed map).
function appendSequenceItem(add_link) {
    deform.appendSequenceItem(add_link);
    var fields = $(add_link.parentNode).children('ul').first().find("input[type=text].map_location");
    fields[fields.length - 1].setAttribute("onblur", "locationTextModified(this);");
    fields[fields.length - 1].map_div = $(add_link.parentNode).children(".location_map")[0];

    var deleteLink = $(fields[fields.length - 1]).parents("li").children('.deformClosebutton')[0];
    deleteLink.setAttribute("onclick", deleteLink.getAttribute("onclick") + " deleteFeature($(this.parentNode).find('input[type=text]')[1].feature);");
}

// Add a map feature (point/polygon) to the map itself as well as updating the most recently added fields (input
// boxes below the map) with the textual representation of the feature.
function addMapFeatures(oid) {
    var fields = $("#" + oid).children('ul').first().find("input[type=text].map_location");
    var map_div = $("#" + oid).children(".location_map")[0];

    var i = 0;
    for (i; i < fields.length; i++) {
        var deleteLink = $(fields[i]).parents("li").children('.deformClosebutton')[0];
        if (deleteLink) { // Check that this hasn't been removed for readonly display
            deleteLink.setAttribute("onclick", deleteLink.getAttribute("onclick") + " deleteFeature($(this.parentNode).find('input[type=text]')[1].feature);");
        }

        fields[i].setAttribute("onblur", "locationTextModified(this);");
        fields[i].map_div = map_div;
//        console.log("Adding " + fields[i].value + " to " + map_div);
        locationTextModified(fields[i]);
    }
//    console.log("Finished adding map features for " + oid);
}

// Update the map feature from the updated textual representation (eg. the latitude was changed so move the point).
function locationTextModified(input) {
    if (input.original_background === undefined) {
        input.original_background = input.style.backgroundColor;
    }

    var geometry_type = input.value.substr(0, input.value.indexOf("("));
    var displayProj = new OpenLayers.Projection("EPSG:4326");
    var proj = new OpenLayers.Projection("EPSG:900913");

    var newGeometry;

    var point_match = /point\([+-]?\d*\.?\d* [+-]?\d*\.?\d*\)/i;
    var poly_match = /polygon\(\(([+-]?\d*\.?\d*\s[+-]?\d*\.?\d*,?\s?)*\)\)/i;
    var line_match = /linestring\(([+-]?\d*\.?\d*\s[+-]?\d*\.?\d*,?\s?)*\)/i;

    var points, text_points, i = 0;
    if (input.value.match(point_match)) {
        points = input.value.trim().substring(geometry_type.length + 1, input.value.trim().length - 1).split(" ");
        newGeometry = new OpenLayers.Geometry.Point(new Number(points[0]), new Number(points[1]));
    } else if (input.value.match(poly_match)) {
        text_points = input.value.trim().substring(geometry_type.length + 2, input.value.trim().length - 2).split(",");
        points = [];
        for (i; i < text_points.length; i++) {
            points.push(new OpenLayers.Geometry.Point(new Number(text_points[i].split(" ")[0]), new Number(text_points[i].split(" ")[1])));
        }
        newGeometry = new OpenLayers.Geometry.Polygon(new OpenLayers.Geometry.LinearRing(points));
    } else if (input.value.match(line_match)) {
        text_points = input.value.trim().substring(geometry_type.length + 1, input.value.trim().length - 1).split(",");
        points = [];
        for (i; i < text_points.length; i++) {
            points.push(new OpenLayers.Geometry.Point(new Number(text_points[i].split(" ")[0]), new Number(text_points[i].split(" ")[1])));
        }
        newGeometry = new OpenLayers.Geometry.LineString(points);
    } else {
        input.style.background = "#ffaaaa";
        return;
    }

    newGeometry.transform(displayProj, proj);
    input.style.background = input.original_background;

    var layer;
    var j = 0, k = 0;
    for (i = 0; i < document.location_maps.length; i++) {
        if (document.location_maps[i].div == input.map_div) {
            for (j; j < document.location_maps[i].layers.length; j++) {
                if ((OpenLayers.Layer.Vector.prototype.isPrototypeOf(document.location_maps[i].layers[j]))) {
                    layer = document.location_maps[i].layers[j];
                    break;
                }
            }
        }
    }

    var new_feature = new OpenLayers.Feature.Vector(newGeometry);

    if (input.hasOwnProperty('feature')) {
        layer.destroyFeatures([input.feature]);
        input.feature = new_feature;
        layer.addFeatures([new_feature]);
    } else {
        input.feature = new_feature;
        layer.addFeatures([new_feature]);
    }
}

// The feature (point/polygon) on the map was modified (using map controls) so update the textual representation of it.
function modifyFeature(object) {
    var feature = object.feature;
    var map = object.object.map;
    var layer = findMapLayerFromFeature(feature, map);
    var oid_node = $(map.div.parentNode);
    var fields = oid_node.children('ul').first().find("input[type=text]");

    var displayProj = new OpenLayers.Projection("EPSG:4326");
    var proj = new OpenLayers.Projection("EPSG:900913");
    var geometry = feature.geometry.clone();
    geometry.transform(map.getProjectionObject(), displayProj);

    var i = 0;
    for (i; i < fields.length; i++) {
        if (fields[i].feature == feature) {
            fields[i].value = geometry;
        }
    }
}

// Delete the feature (point/polygon) from both the map and the sequence (input boxes below the map).
function deleteFeature(feature) {
    var layer = findMapLayerFromFeature(feature);

    var map = findMapFromLayer(layer);
    var displayProj = new OpenLayers.Projection("EPSG:4326");

    var oid_node = $(map.div.parentNode);
    var geometry = feature.geometry.clone();
    geometry.transform(map.getProjectionObject(), displayProj);

    var fields = oid_node.children('ul').first().find("input[type=text]");
    var i = 0;
    for (i; i < fields.length; i++) {
        if (fields[i].value == geometry.toString()) {
            deform.removeSequenceItem($(fields[i].parentNode.parentNode.parentNode.parentNode.parentNode).find(".deformClosebutton"));
        }
    }

    feature.destroy();
}

// A new feature (point/polygon) was added to the map, if the feature isn't already associated with an input add a new
// item to the sequence and associate it with the given feature (the feature may already be associated if a map control
// fires featureInserted events even though the feature was only moved).
function featureInserted(object) {
    var feature = object.feature;
    var displayProj = new OpenLayers.Projection("EPSG:4326");
    var proj = new OpenLayers.Projection("EPSG:900913");
    var map = object.object.map;
    var layer = feature.layer; //findMapLayerFromFeature(feature, map);

    var oid_node = $(map.div.parentNode);
    var fields = oid_node.children('ul').first().find("input[type=text].map_location");

    // Check if this feature already has an associated input
    var i = 0;
    for (i; i < fields.length; i++) {
//        var tmp = feature.geometry.clone();
//        tmp.transform(map.getProjectionObject(), displayProj);
        if (fields[i].feature == feature) {
            return;
        }
    }


//            var i = 0, j = 0;
//            for (i; i < layer.features.length; i++) {
//                /*alert((OpenLayers.Geometry.Polygon.prototype.isPrototypeOf(layer.features[i].geometry)));*/
//                alert(layer.features[i].geometry);
//                alert(displayProj + " : " + proj + " : " + map.getProjection() + " : " + map.getProjectionObject());
//                for (j; j < layer.features[i].geometry.getVertices().length; j++) {
//                    vertices += layer.features[i].geometry.getVertices()[j].transform(map.getProjectionObject(),displayProj) + ", ";
//                }
//            }
    /*   alert(vertices);*/


    // Only add a new feature if the last item in the list isn't blank
    var last_field = fields[fields.length - 1];
    var siblings = $(last_field.parentNode.parentNode).siblings().find("input[type=text]");
    if (last_field.value != '' || last_field.feature !== undefined || siblings[0].value != '' || siblings[1].value != '') {
        /* Add the feature */
        appendSequenceItem(oid_node.children(".deformSeqAdd")[0]);
    }

    fields = oid_node.children('ul').first().find("input[type=text].map_location");

    var geometry = feature.geometry.clone();
    geometry.transform(map.getProjectionObject(), displayProj);


    fields[fields.length - 1].value = geometry;
    fields[fields.length - 1].feature = feature;
    fields[fields.length - 1].className = fields[fields.length - 1].className.replace( /(?:^|\s)placeholder_text(?!\S)/g , '' );
}

//--------------------conditional_heckbox_mapping.pt----------------
function displayConditionalCheckboxItems(checkboxElement) {
    var contentDiv = $(checkboxElement.parentNode).children(".checkbox_mapping_content")[0];
    if (checkboxElement.checked) {

//        if (contentDiv.hasOwnProperty('previousContent')) {
//            contentDiv.innerHTML = contentDiv.previousContent;
//            processJavascript(contentDiv);
//            deform.processCallbacks();
//        } else {
        var prototypes = $(checkboxElement.parentNode).children(".checkbox_mapping_prototypes").children(".checkbox_mapping_prototype");

        var content = "";
        var i = 0;
        for (i; i < prototypes.length; i++) {
            content += prototypes[i].value;
        }
        contentDiv.innerHTML = content;
        processJavascript(contentDiv);
        deform.processCallbacks();
//        }

    } else {
        contentDiv.previousContent = contentDiv.innerHTML;
        contentDiv.innerHTML = "";
    }
}

////------------------select_mapping.pt---------------------------
//function setSelectedItem(select_element) {
//    var protos = $("#select_mapping_prototypes-" + select_element.id).children(".select_mapping_prototype");
//
//    var i = 0;
//    var selectedProto;
//    for (i; i < protos.length; i++) {
//        if (protos[i].id.indexOf(select_element.value) >= 0) {
//            selectedProto = protos[i];
//            break;
//        }
//    }
//    if (selectedProto == undefined) {
//        return;
//    }
//
////     var newHTML = (typeof selectedProto == 'undefined' ? "" : selectedProto.value);
////    alert($(selectedProto).attr('prototype'));
//    $(selectedProto).attr('prototype', encodeURIComponent($(selectedProto).attr('prototype')));
//    var $proto_node = $(selectedProto);
//    var $before_node = $("#select_mapping_content-" + select_element.id).find('.deformInsertBefore');
//    var min_len = parseInt('0');
//    var max_len = parseInt('9999');
//    var now_len = parseInt('0');
//    deform.addSequenceItem($proto_node, $before_node);
//
////     document.getElementById("select_mapping_content-" + select_element.id).innerHTML = newHTML;
//
////    var scripts = $("#select_mapping_content-" + select_element.id).find("script");
////
////    for (i = 0; i < scripts.length; i++) {
////        if (scripts[i].innerHTML.trim().length > 0) {
////            eval(scripts[i].innerHTML);
////        } else if (scripts[i].src.length > 0) {
////            $.getScript(scripts[i].src);
////        }
////    }
////    processJavascript($("#select_mapping_content-" + select_element.id)[0]);
////    deform.processCallbacks();
//}

// Read all javascript in the given HTML element and run it (eg. when adding new sequence items).
function processJavascript(parentElement) {
    var scripts = $(parentElement).find("script");

    for (i = 0; i < scripts.length; i++) {
        if (scripts[i].innerHTML.trim().length > 0) {
            eval(scripts[i].innerHTML);
        } else if (scripts[i].src.length > 0) {
            $.getScript(scripts[i].src);
        }
    }
}

//--------------multi_select_sequence.pt----------------------------------------------
// The add button was pressed to add a multi-sequence item (eg. SEO/FOR codes)
function buttonPressed(node) {
    var oid_node = $(node).parent();
    var id = oid_node.attr('id');

    var first_select = oid_node.children(".first_field")[0];
    var second_select = oid_node.children(".second_field")[0];
    var third_select = oid_node.children(".third_field")[0];

    var fields = oid_node.children('ul').first().find("input[readonly='readonly']");

    var text = third_select.options[third_select.selectedIndex].value;

    if (text == "---Select One---") {
        var text = second_select.options[second_select.selectedIndex].value;
    }

    fields[fields.length - 1].value = text;
    fields[fields.length - 1].style.display = "inline";
    var removeButton = $(fields[fields.length - 1]).parents('[id^="sequence"]').find(".deformClosebutton")[0];
    removeButton.setAttribute("onclick","deform.removeSequenceItem(this);" + "showAdd('" + id + "', false);");
//    removeButton.onclick = removeButton.onclick + "; showAdd(" + oid_node[0].id + ", false); ";

    /* Delete duplicates */
    var i = 0;
    for (i; i < fields.length - 1; i++) {
        if (fields[i].value == text) {
            deform.removeSequenceItem($(fields[i]).parents('[id^="sequence"]').find(".deformClosebutton")[0]);
            alert("Not Added: The selected FOR code is a duplicate");
        }
    }
    /* Reset the FOR field select boxes */
    first_select.selectedIndex = 0;
    second_select.innerHTML = "";
    second_select.style.display = "none";
    $(second_select).next().hide();
    third_select.innerHTML = "";
    third_select.style.display = "none";
    $(third_select).next().hide();

    showAdd(oid_node[0].id, false);
}

// Make multi-select (eg. SEO/FOR codes) elements hide the add button when an item is deleted.
function fix_multi_select_close(oid) {
    var oid_node = $('#' + oid);
    var close_buttons = oid_node.children('ul').first().find("span.deformClosebutton");
    for (var i=0; i<close_buttons.length; i++) {
        close_buttons[i].setAttribute("onclick","deform.removeSequenceItem(this);" + "showAdd('" + oid + "', false);");
    }
}

// Show/Hide the add button for the multi-select identified by oid
function showAdd(oid, show) {
    var oid_node = $('#' + oid);
//    alert(oid_node);

    var $before_node = oid_node.children('ul').first().children('.deformInsertBefore').first();
    var max_len = parseInt($before_node.attr('max_len')||'9999', 10);
    var now_len = parseInt($before_node.attr('now_len')||'0', 10);
    if (now_len >= max_len) {
        oid_node.children("button").hide();
        oid_node.children(".max_error").show();
        return;
    }
    oid_node.children(".max_error").hide();

    if (show) {
        oid_node.children("button")[0].style.display = "inline";
        var original_color = oid_node.children("button").first().css('backgroundColor');
        oid_node.children("button").animate({ backgroundColor: "#F7931E"}, 100);
        oid_node.children("button").animate({ backgroundColor: original_color}, 100);
        oid_node.children("button").animate({ backgroundColor: "#F7931E"}, 100);
        oid_node.children("button").animate({ backgroundColor: original_color}, 100);

//        alert('show');
    } else {
//        alert('hide');
        oid_node.children("button")[0].style.display = "none";
    }
}

// Set the multi-select display appropriately for when the second field is selected.
function updateSecondFields(oid) {
    var oid_node = $('#' + oid);

    var first_select = oid_node.children(".first_field")[0];
    var second_select = oid_node.children(".second_field")[0];
    var third_select = oid_node.children(".third_field")[0];

    if (first_select.selectedIndex != 0) {
        var options_class = "second_level_data-" + first_select.options[first_select.selectedIndex].value;
        var second_level_options = document.getElementsByClassName(options_class)[0];
        second_select.innerHTML = second_level_options.innerHTML;
        second_select.style.display = "inline";
        $(second_select).next().show();
    } else {
        second_select.innerHTML = "";
        first_select.selectedIndex = 0;
        second_select.style.display = "none";
        $(second_select).next().hide();
        showAdd(oid, false);
    }
    third_select.innerHTML = "";
    third_select.style.display = "none";
    $(third_select).next().hide();
    /* Make sure that the user can't have an invalid 3rd field selected when the first select is changed */
}

// Set the multi-select display appropriately for when the third field is selected.
function updateThirdFields(oid) {
    var oid_node = $('#' + oid);

    var first_select = oid_node.children(".first_field")[0];
    var second_select = oid_node.children(".second_field")[0];
    var third_select = oid_node.children(".third_field")[0];

    if (second_select.selectedIndex != 0) {
        var options_class = "third_level_data-" + second_select.options[second_select.selectedIndex].value;
        var third_level_options = document.getElementsByClassName(options_class)[0];
        third_select.innerHTML = third_level_options.innerHTML;
        third_select.style.display = "inline";
        $(third_select).next().show();
    } else {
        third_select.innerHTML = "";
        third_select.style.display = "none";
        $(third_select).next().hide();
        showAdd(oid, false)
    }
}

//---------------------CHECKED CONDITIONAL INPUT---------------------
function conditionalCheckboxToggled(checkbox) {
    var inverted = $(checkbox).siblings(".show_on_selected")[0];
    inverted = (inverted !== undefined && inverted.value == 'true');
    var show = inverted && checkbox.checked || !inverted && !checkbox.checked;
    var next_element = $(checkbox).parent().next();

    var DURATION = 300;
    if (show) {
        next_element.show(DURATION);
    } else {
        next_element.hide(DURATION);
    }
}

//-------------------CHOICE MAPPING ITEM-------------------------
function choice_selected(list_item, is_onchange, is_loading) {
    var oid = list_item.id.replace("item-", "");
    var radio_element = $(list_item).children('input[type=radio]').first();
    var selected_element = $(list_item).siblings().find("[name*='selected_sampling']").first();
    selected_element[0].value = $(list_item).attr('select_name');
    if (!radio_element.attr('checked') || is_onchange) {
        radio_element.attr('checked', 'checked');
        var prototype = $("#" + oid + "-prototype").attr('prototype');

        var content_element = $('#' + oid + '-content')[0];
        content_element.innerHTML = prototype;
        if ($(content_element).children().first().is("fieldset")) {
            $(content_element).children().first().children("legend").remove();
        }

        process_callbacks_when_ready(content_element);
        content_element.processed = true;
    }
    var other_radios = $("[name='" + radio_element[0].name + "']").not("#select-" + oid);
    for (var i=0; i<other_radios.length; i++) {
        set_prototype(other_radios[i].id.replace("select-", ""));
    }
}

function process_callbacks_when_ready(content_element) {
    if (deform.callbacks.length > 0) {
        window.setTimeout(process_callbacks_when_ready, 200, content_element);
    } else {
        processJavascript(content_element);
        deform.processCallbacks();
    }
}

function set_prototype(oid) {
    var content_element = $('#' + oid + '-content')[0];
    if (content_element.innerHTML) {
//                $("#" + oid + "-prototype").attr('prototype', content_element.innerHTML);
//                alert(content_element.innerHTML);
        content_element.innerHTML = '';
    }
}


//--------------------METHOD SCHEMA FIELD ITEM--------------------
function conditional_display(oid) {
//            alert(oid);
    var list_item = $("#item-" + oid)[0];
//            alert(list_item);
    if (list_item) {
        var list = list_item.parentNode;
//                alert(list);
        var type = $(list).find(".field_type")[0];
//                alert(type.value);

        var units = $(list).find('.custom_field_units')[0].parentNode.parentNode;
        var example = $(list).find('.custom_field_example')[0].parentNode.parentNode;
        var default_item = $(list).find('.custom_field_default')[0].parentNode.parentNode;
//                var validator = $(list).find('.custom_field_validators')[0].parentNode.parentNode;
        var values = $(list).find('.custom_field_values')[0].parentNode.parentNode;

        $(units).find('label')[0].innerHTML = 'Units'

        switch (type.value) {
            case "integer":
            case "decimal":
            case "hidden":
                example.className += " hidden";
                default_item.className = values.className.replace( / hidden/g , '');
//                        validator.className = values.className.replace( /\shidden/g , '');
                units.className = values.className.replace( /\shidden/g , '');
                values.className += " hidden";
                break;
            case "text_input":
            case "text_area":
                example.className = values.className.replace( / hidden/g , '');
                default_item.className = values.className.replace( / hidden/g , '');
//                        validator.className = values.className.replace( / hidden/g , '');
                units.className += " hidden";
                values.className += " hidden";
                break;

            case "select":
            case "radio":
                example.className += " hidden";
                default_item.className = values.className.replace( / hidden/g , '');
//                        validator.className = values.className.replace( / hidden/g , '');
                units.className += " hidden";
                values.className = values.className.replace( / hidden/g , '');
                break;

            case "website":
            case "email":
            case "phone":
            case "date":
                example.className += " hidden";
                default_item.className = values.className.replace( / hidden/g , '');
//                        validator.className += " hidden";
                units.className += " hidden";
                values.className += " hidden";
                break;

            case "file":
                example.className = values.className.replace( / hidden/g , '');
                default_item.className += " hidden";
//                        validator.className += " hidden";
                units.className = values.className.replace( / hidden/g , '');
                $(units).find('label')[0].innerHTML = 'Mime Type';
                values.className += " hidden";
                break;

            case "checkbox":
                example.className += " hidden";
                default_item.className = values.className.replace( / hidden/g , '');
//                        validator.className = values.className.replace( / hidden/g , '');
                units.className += " hidden";
                values.className += " hidden";
                break;
        }
    }
}

//----------------------------METHOD SCHEM PARENTS SEQUENCE--------------------
function updateParentItem(add_button) {
    var select_element=$(add_button.parentNode).children('select').first()[0];
    var selected_option = select_element.options[select_element.selectedIndex];

    var parents = $(add_button.parentNode).find('ul').first().children("li");
    var name_element = parents.last().find("[name='methodschema:name']")[0];
    var id_element = parents.last().find("[name='methodschema:id']")[0];
    name_element.value = selected_option.innerHTML;
    id_element.value = selected_option.value;

    parents.last().find(".parent_schema_preview_panel .preview_content")[0].innerHTML = selected_option.attributes['prototype'].value;
//            $(add_button.parentNode).find('ul').first().find('span input:first')[0].value=selected_option.value;

    // Remove duplicates
    for (var i = 0; i < parents.length; i++) {
//                $(selected_option.parentNode).find("option:contains('"+fields[i].value+"')").attr({disabled: 'disabled'});
//                $(selected_option.parentNode).find("option:contains('"+fields[i].value+"')").hide(0)

        if ($(parents[i]).find("[name='methodschema:name']")[0].value == name_element.value && $(parents[i]).find("[name='methodschema:name']")[0] != name_element) {
            parents.last()[0].innerHTML = "<p class='error'>Cannot add duplicate parent schemas.</p>";
            parents.last().delay(2000);
            parents.last().hide(500, function(){$(parents[i]).parents(".deformSeq-schema_parents li").remove();});
        }
    }
}


//--------------------MINT AUTOCOMPLETE INPUT--------------------------
function get_name_from_identifier(oid, identifier, url) {
    $.ajax({
        url: url + identifier,
        dataType: "json",
        success: function( data ) {
            var data_all = data['result-metadata']['all'];
            var value = "";
            if (identifier.match(/.*people.*/g)) {
                value = data_all['Honorific'][0] + " " + data_all['Given_Name'][0] + " ";
                for (var i=0; i<data_all['Other_Names'].length; i++) {
                    if (data_all['Other_Names'][i].trim().length > 0) {
                        value += data_all['Other_Names'][i] + " ";
                    }
                }
                value = value.trim() + " " + data_all['Family_Name'][0];
            } else if (identifier.match(/.*activities.*/g)) {
                value = data['dc:title'];
            }

            $("#" + oid + "-autocomplete")[0].value = value;


//                    $('#' + oid).siblings("a.mint-more-info")[0].href = data['rdf:about'];
            $('#' + oid).siblings("a.mint-more-info").removeClass('hidden');

            var more_info_panel = $('#' + oid).siblings("div.more_info_panel");
            more_info_panel.children().remove();

            more_info_panel.append("<div><b>Name:</b> " + value + "</div>");
            if (data_all['Email'] && data_all['Email'][0].length > 0) {
                more_info_panel.append("<div><b>Email:</b> <a href='mailto:" + data_all['Email'][0] + "'>" + data_all['Email'] + "</div>");
            }
            if (data_all['dc_description'] && data_all['dc_description'][0].length > 0) {
                more_info_panel.append("<div><b>Description:</b>" + data_all['dc_description'][0] + "</div>");
            }

            var links_panel = "<div><b>Links:</b> <ul>";
            if (data_all['Personal_Homepage'] && data_all['Personal_Homepage'][0]) {
                links_panel += "<li><a style='overflow: hidden;' target='_blank' href='" + data_all['Personal_Homepage'][0] + "'>Personal Homepage</li>";
            }
            if (data_all['Staff_Profile_Homepage'] && data_all['Staff_Profile_Homepage'][0]) {
                links_panel += "<li><a style='overflow: hidden;' target='_blank' href='" + data_all['Staff_Profile_Homepage'][0] + "'>Staff Profile</li>";
            }
            if (data_all['Personal_URI'] && data_all['Personal_URI'][0]) {
                links_panel += "<li><a style='overflow: hidden;' target='_blank' href='" + data_all['Personal_URI'][0] + "'>Personal URI</li>";
            }
            links_panel += "<li><a style='overflow: hidden;' target='_blank' href='" + data['rdf:about'] + "'>Mint Record</li>";

            links_panel += "</ul></div>";
            more_info_panel.append(links_panel);

            var onclick = '$("#' + oid + '").siblings(".more_info_panel").hide(); $("#' + oid + '").siblings("a").removeClass("current");';
            var close = "<div class='close_button buttonText' onclick='" + onclick + "' >Close</div>";
            more_info_panel.append(close);
        },
        error: function(jqXHR, textStatus, errorThrown) {
//                    alert(textStatus);
//                    alert(errorThrown);
            console.error("Error looking up mint identifier: " + textStatus);
        }
    });
}

function lookup_mint(url, request, response) {
    $.ajax({
        url: url + request.term,
        dataType: "json",
        success: function( data ) {
            if (data.length == 0) {
                return response([{
                    label: "None available",
                    value: "",
                    identifier: ""
                }]);
            }

            response($.map( data, function( item ) {
                return {
                    label: item.label,
                    value: item.label,
                    identifier: item.value
                }
            }));
        },
        error: function(jqXHR, textStatus, errorThrown) {
            return response([{
                label: "None available",
                value: "",
                identifier: ""
            }]);
        },
        open: function() {
            $( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" );
        },
        close: function() {
            $( this ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" );
        }
    });
}

function partial(func /*, 0..n args */) {
    var args = Array.prototype.slice.call(arguments, 1);
    return function() {
        var allArguments = args.concat(Array.prototype.slice.call(arguments));
        return func.apply(this, allArguments);
    };
}

function mint_autocomplete_selected(event, ui){
    $("#"+ event.target.id.replace("-autocomplete", ""))[0].value = ui.item.identifier;
    get_name_from_identifier(event.target.id.replace("-autocomplete", ""), ui.item.identifier);
}

//------------------SHARING SEQUENCE----------------------
function autocomplete_selected(event, ui) {
    var element = $(event.target);
    element[0].value = ui.item.label;
    element.prev('input')[0].value = ui.item.identifier;
}

function add_user(add_button) {
    var oid = add_button.id.replace("-seqAdd", "");
    var user_id = $("#" + oid + "-userSelectionId")[0].value;
    var user_name = $("#" + oid + "-userSelection")[0].value;
    $(add_button.parentNode).children("ul").first().children(".deformInsertBefore").prev().find("[name='user_id']")[0].value=user_id;
    $(add_button.parentNode).children("ul").first().children(".deformInsertBefore").prev().find("legend")[0].innerHTML=user_name;
}