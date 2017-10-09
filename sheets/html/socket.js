let socket;
let socketStatus;

function openSocket() {
  if (socket) {
    socket.onclose = null;
    socket.close();
    socket = null;
  }
  console.log("Opening socket");
  sendSocketStatus("OPENING");
  let _socket = new WebSocket("ws://localhost:10101");
  _socket.onopen = () => {
    socket = _socket;
    sendSocketStatus("OPENED");
    console.log("Connected to WebSocket");
  };
  _socket.onmessage = (event) => {
    incoming(JSON.parse(event.data));
  };
  _socket.onclose = (reason) => {
    console.log("Closed:", reason, "reopening...");
    socket = null;
    sendSocketStatus("REOPENING");
    setTimeout(openSocket, 100);
  };
}

function registerSocketListener(callback) {
  registerSocketListener.callbacks.push(callback);
  callback(socketStatus);
}
registerSocketListener.callbacks = [];

function sendSocketStatus(newStatus) {
  if (newStatus) {
    socketStatus = newStatus;
  }
  for (let callback of registerSocketListener.callbacks) {
    callback(socketStatus);
  }
}

sendSocketStatus("INIT");

function incoming(o) {
  let commandName = o.command;
  let CommandClass = AllCommands[commandName];
  if (!CommandClass || CommandClass.__proto__ !== Command) {
    console.warn("Bad command", o.command, "resolves to:", CommandClass);
    return;
  }
  let command = new CommandClass(o);
  console.log("Incoming:", command);
  model.setConnectionDirection("down");
  model.applyCommand(command);
}

function send(command) {
  if (!command || (!(command instanceof Command))) {
    throw new Error(`Bad command: ${command}`);
  }
  model.setConnectionDirection("down");
  model.applyCommand(command);
  console.log("Send:", command);
  let j = JSON.stringify(command);
  socket.send(j);
}
