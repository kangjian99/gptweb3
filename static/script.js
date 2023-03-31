/*
let loading = document.getElementById('loading');
let form = document.querySelector('form');
form.addEventListener('submit', () => {
    loading.style.display = 'block';
});
*/

function copyToClipboard() {
  var resHtml = document.getElementById("res").innerHTML;
  var tmpElement = document.createElement('div');
  tmpElement.innerHTML = resHtml;
  document.body.appendChild(tmpElement);
  tmpElement.style.background = '#fff';
  tmpElement.style.position = 'absolute';
  tmpElement.style.left = '-9999px';
  var range = document.createRange();
  range.selectNodeContents(tmpElement);
  var selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  document.execCommand('copy', false, 'text/html');
  document.body.removeChild(tmpElement);
  var animation = document.getElementById("copy-animation");
  animation.classList.remove("hide");
  setTimeout(function() {
    animation.classList.add("hide");
  }, 2000);  // 2 秒后隐藏提示框
}


var dropdown = document.getElementById("dropdown");
var pid = dropdown.getAttribute("data-pid");
var pid_list = pid.split(",");
for (var i = 1; i <= pid_list.length; i++) {
  var option = document.createElement("option");
  option.text = pid_list[i-1];
  option.value = i;
  dropdown.add(option);
}