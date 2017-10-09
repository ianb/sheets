// shortcuts with: https://craig.is/killing/mice

function runAll() {
  names = Array.from(model.files.keys());
  names.sort();
  for (let name of names) {
    executeFile(name);
  }
}

let model = new Model();

openSocket();

function updateFile(filename, content) {
  let command = new FileEdit({filename, content});
  if (!model.files.get(filename)) {
    model.files.set(filename, {});
  }
  model.files.get(filename).content = content;
  send(command);
}

function deleteFile(filename) {
  let command = new FileDelete({filename});
  send(command);
}

function executeFile(filename, subexpressions) {
  let command = new ExecutionRequest({
    filename,
    content: model.files.get(filename).content,
    subexpressions,
  });
  send(command);
}

registerSocketListener((newStatus) => {
  model.connectionLive = newStatus == "OPENED";
  if (window.render) {
    render();
  }
});

if (typeof render == "undefined") {
  window.render = function (...args) {
    setTimeout(() => {
      render(...args);
    }, 100);
  };
}
