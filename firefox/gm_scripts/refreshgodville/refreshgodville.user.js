// ==UserScript==
// @name        refreshgodville
// @namespace   godville
// @description Auto-closes Godville Hero screen when opened just for refresh
// @include     https://godville.net/superhero#refresh
// @version     1
// @grant       window.close
// ==/UserScript==

function check_load_state() {
  var search_block = document.getElementById('search_block');
  if(search_block != undefined) {
    if(search_block.style.display == 'none') {
      console.log("Closing window...");
      // Following line would no work in Firefox without about:config dom.allow_scripts_to_close_windows=true
      window.close();
    } else {
      console.log("Still searching for hero, wait for a sec...");
      setTimeout(check_load_state, 1000);
    }
  } else {
    console.log("Did not found #search_block");
  }
}

if(window.location.href.substr(-8) == '#refresh') {
  setTimeout(check_load_state, 1000);  
} else {
  console.log("Not a #refresh target!");
}
