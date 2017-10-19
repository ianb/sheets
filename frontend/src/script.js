import { model, FileEdit, FileDelete, ExecutionRequest } from './datalayer';
import { openSocket, registerSocketListener, send } from './socket';

function runAll() {
  names = Array.from(model.files.keys());
  names.sort();
  for (let name of names) {
    executeFile(name);
  }
}

openSocket();

export function updateFile(filename, content) {
  let command = new FileEdit({filename, content});
  if (!model.files.get(filename)) {
    model.files.set(filename, {});
  }
  model.files.get(filename).content = content;
  send(command);
}

export function deleteFile(filename) {
  let command = new FileDelete({filename});
  send(command);
}

export function executeFile(filename, subexpressions) {
  let command = new ExecutionRequest({
    filename,
    content: model.files.get(filename).content,
    subexpressions,
  });
  send(command);
}

registerSocketListener((newStatus) => {
  model.connectionLive = newStatus == "OPENED";
  if (window.renderPage) {
    renderPage();
  }
});
