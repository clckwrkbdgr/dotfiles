// ==UserScript==
// @name        vk download full album
// @namespace   vk
// @description For auto-downloading full albums which have some non-playing tracks
// @include     https://vk.com/*#badger
// @version     1
// @grant       none
// ==/UserScript==

var DEBUG = false;

// Works only with VK Music Download add-on.
function try_to_download() {
  var span_download_all = document.getElementsByClassName('download_all');
  if(span_download_all != undefined) {
    console.log("Downloading...");
    span_download_all = span_download_all[0];
	if(!DEBUG) {
		span_download_all.click();
	} else {
		console.log("DEBUG: clicked 'Download All'.");
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
		setTimeout(function() { console.log("Closing window..."); window.close(); }, 1000);
	} else {
		console.log("DEBUG: waiting to close.");
	}
  } else {
    console.log("Did not found .download_all, trying again in 1 sec...");
    setTimeout(try_to_download, 1000);
  }
}

if(window.location.href.substr(-7) == '#badger') {
  setTimeout(try_to_download, 1000);
} else {
  console.log("Not a #badger target!");
}
