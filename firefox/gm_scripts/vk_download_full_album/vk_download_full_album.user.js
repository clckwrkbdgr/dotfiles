// ==UserScript==
// @name        vk download full album
// @namespace   vk
// @description For auto-downloading full albums which have some non-playing tracks
// @include     https://vk.com/*#badger
// @version     1
// @grant       none
// ==/UserScript==

// Works only with VK Music Download add-on.
function try_to_download() {
  var span_download_all = document.getElementsByClassName('download_all');
  if(span_download_all != undefined) {
    console.log("Downloading...");
    span_download_all = span_download_all[0];
    span_download_all.click();
    // Following line would no work in Firefox without about:config dom.allow_scripts_to_close_windows=true
    setTimeout(function() { console.log("Closing window..."); window.close(); }, 1000);
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
