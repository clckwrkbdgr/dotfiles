// ==UserScript==
// @name        diary
// @namespace   diary
// @include     http://*.diary.ru/*
// @version     1
// @grant       none
// ==/UserScript==

var comment_area_button = $("div#addCommentArea_title");
if(comment_area_button != undefined) {
	comment_area_button.click(function() {
		var comment_area = $("div#addCommentArea div.formcontainer");
		if(comment_area.is(":visible")) {
			comment_area.hide();
		} else {
			comment_area.show();
		}	
	});
	comment_area_button.click();
}
