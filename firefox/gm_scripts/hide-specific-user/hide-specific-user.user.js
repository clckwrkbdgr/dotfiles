// ==UserScript==
// @name        hide-specific-user
// @namespace   lor
// @include     https://www.linux.org.ru/*
// @version     1
// @grant       none
// ==/UserScript==

// User script for hiding comments of unwanted user.
// Such user should have '%ignore%' in their remark.

var messages = document.getElementsByClassName("msg");
for(var i = 0; i < messages.length; ++i) {
  var message = messages[i];
  var containers = message.getElementsByClassName("msg-container");
  if(containers == undefined || containers.length < 1) {
    continue;
  }
  var container = containers[0];
  var remark = container.getElementsByClassName("user-remark");
  console.log(remark);
  if(remark == undefined || remark.length < 1) {
    continue;
  }
  remark = remark[0];  
  console.log(remark.textContent);
  if(remark.textContent.contains('%ignore%')) {
    message.style.display = 'none';
  }
}
console.log("hide-specific-user userscript is set successfully.");
