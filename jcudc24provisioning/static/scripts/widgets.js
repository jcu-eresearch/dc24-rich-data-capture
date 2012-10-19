/**
 * Created with IntelliJ IDEA.
 * User: xjc01266
 * Date: 24/09/12
 * Time: 4:44 PM
 * To change this template use File | Settings | File Templates.
 */


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

function submitClearsDefaultValues(oid, default_text) {
    var form = document.getElementById('deform');
    default_text = escapeQuotes(default_text);

    var submit_text = "if (document.getElementById('" + oid + "').value == '" + default_text + "') {document.getElementById('" + oid + "').value = '';}";

    if (form.getAttribute('onsubmit') != null) {
        submit_text += form.getAttribute('onsubmit');
    }
    form.setAttribute('onsubmit', submit_text);
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
