Mousetrap.bind(['ctrl+shift+a', 'command+shift+a'], () => {
  runAll();
  return false;
});

Mousetrap.bind('tab', (event) => {
  if (event.target.tagName == "TEXTAREA") {
    insertAtCursor(event.target, "    ");
    return false;
  }
});

Mousetrap.bind(["ctrl+?", "ctrl+/"], () => {
  model.showHelp = !model.showHelp;
  render();
  return false;
});

Mousetrap.bind("ctrl+e", (event) => {
  let el = event.target;
  if (model.focusName) {
    el = document.querySelector(`.file[data-name="${model.focusName}"]`) || el;
  }
  while (el) {
    if (el.classList && el.classList.contains("file")) {
      break;
    }
    el = el.parentNode;
  }
  if (!el) {
    return;
  }
  el.dispatchEvent(new CustomEvent("collapse"));
  setTimeout(() => {
    el.focus();
  }, 100);
  return false;
});

Mousetrap.bind("shift+ctrl+e", () => {
  let allCollapsed = true;
  for (let name of model.files.keys()) {
    el = document.querySelector(`.file[data-name="${name}"]`);
    if (!el.getAttribute("data-collapsed")) {
      allCollapsed = false;
    }
    el.dispatchEvent(new CustomEvent("collapse-down"));
  }
  if (allCollapsed) {
    for (let name of model.files.keys()) {
      el = document.querySelector(`.file[data-name="${name}"]`);
      el.dispatchEvent(new CustomEvent("collapse"));
    }
  }
});

Mousetrap.bind("ctrl+t", (event) => {
  model.showNavigation = !model.showNavigation;
  render();
});

Mousetrap.bind("escape", (event) => {
  model.showNavigation = model.showHelp = false;
  render();
});

function insertAtCursor(field, text) {
  // From https://stackoverflow.com/questions/11076975/insert-text-into-textarea-at-cursor-position-javascript
  if (field.selectionStart || field.selectionStart === 0) {
    let startPos = field.selectionStart;
    let endPos = field.selectionEnd;
    field.value = field.value.substring(0, startPos)
      + text
      + field.value.substring(endPos);
    field.selectionStart = field.selectionEnd = endPos + text.length - (endPos - startPos);
  } else {
    myField.value += text;
  }
}
