document.addEventListener("DOMContentLoaded", function () {
  var input = document.getElementById("hardware_id");
  if (!input) return;

  function format(value) {
    var clean = value.toUpperCase().replace(/[^A-Z0-9]/g, "");
    var groups = clean.match(/.{1,4}/g) || [];
    return groups.join("-");
  }

  input.addEventListener("input", function () {
    var caret = input.selectionStart;
    var cleanBefore = input.value.slice(0, caret).toUpperCase().replace(/[^A-Z0-9]/g, "").length;

    input.value = format(input.value);

    var seen = 0, pos = input.value.length;
    for (var i = 0; i < input.value.length; i++) {
      if (input.value[i] !== "-") seen++;
      if (seen === cleanBefore) { pos = i + 1; break; }
    }
    input.setSelectionRange(pos, pos);
  });
});
