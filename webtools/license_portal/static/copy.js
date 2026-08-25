document.addEventListener("click", function (event) {
  var button = event.target.closest("[data-copy-target]");
  if (!button) return;

  var field = document.getElementById(button.getAttribute("data-copy-target"));
  if (!field) return;

  navigator.clipboard.writeText(field.value).then(function () {
    var original = button.textContent;
    button.textContent = "Copied";
    button.classList.add("copied");
    setTimeout(function () {
      button.textContent = original;
      button.classList.remove("copied");
    }, 1500);
  });
});
