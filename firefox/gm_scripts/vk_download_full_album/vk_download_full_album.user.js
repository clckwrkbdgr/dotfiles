// ==UserScript==
// @name        vk download full album
// @namespace   vk
// @description For auto-downloading full albums which have some non-playing tracks
// @include     https://vk.com/*#badger*
// @version     1
// @grant       none
// ==/UserScript==

var DEBUG = false;

// Works only with VK Music Download add-on.
function try_to_download() {
  var specific_request = /#badger([01]*)$/g.exec(window.location.href);
  if(specific_request != undefined) {
	  specific_request = specific_request[1];
  }
  var specific_request_index = 0;
  var span_download_all = document.getElementsByClassName('download_all');
  if(span_download_all != undefined) {
    console.log("Downloading...");
	  
	if(specific_request == "") {
      span_download_all = span_download_all[0];
	  if(!DEBUG) {
	  	  span_download_all.click();
	  } else {
	  	  console.log("DEBUG: clicked 'Download All'.");
	  }
	} else {
		var wall_text = document.getElementsByClassName('wall_text')[0];
		var buttons = wall_text.getElementsByClassName('dwn_btn');
    	for(var i = 0; i < buttons.length; ++i) {
			var button = buttons[i];
			if(specific_request_index < specific_request.length && specific_request[specific_request_index] == "0") {
				console.log("Downloading requested track " + specific_request_index + "...");
				if(!DEBUG) {
					button.click();
				} else {
					console.log("DEBUG: clicked on specific track in wall_text.");
				}
			}
			++specific_request_index;
		}
	}
	  
	var replies = document.getElementsByClassName('reply');
	for(var i = 0; i < replies.length; ++i) {
		var reply = replies[i];
		var downloads = reply.getElementsByClassName('dwn_btn');
		if(downloads.length > 0) {
			for(var j = 0; j < downloads.length; ++j) {
				var btn = downloads[j];
				console.log("Found another track in replies.");
				if(!DEBUG) {
					btn.click();
				} else {
					console.log("DEBUG: clicked on track in reply.");
				}
			}
		} else {
			console.log("Found reply without downdloads, breaking the loop.");
			break;
		}
	}
	if(!DEBUG) {
		// Following line would no work in Firefox without about:config dom.allow_scripts_to_close_windows=true
		setTimeout(function() { console.log("Closing window..."); window.close(); }, 2000);
	} else {
		console.log("DEBUG: waiting to close.");
	}
  } else {
    console.log("Did not found .download_all, trying again in 1 sec...");
    setTimeout(try_to_download, 1000);
  }
}

if(/#badger[01]*$/.test(window.location.href)) {
  setTimeout(try_to_download, 1000);
} else {
  console.log("Not a #badger target! URL: " + window.location.href);
}
