let socket;

function openSocket() {
  if (socket) {
    socket.onclose = null;
    socket.close();
    socket = null;
  }
  console.log("Opening socket");
  let _socket = new WebSocket("ws://localhost:10101");
  _socket.onopen = () => {
    socket = _socket;
    console.log("Connected to WebSocket");
  };
  _socket.onmessage = (event) => {
    incoming(JSON.parse(event.data));
  };
  _socket.onclose = (reason) => {
    console.log("Closed:", reason, "reopening...");
    socket = null;
    setTimeout(openSocket, 100);
  };
}

function incoming(o) {
  let commandName = o.command;
  let CommandClass = AllCommands[commandName];
  if (!CommandClass || CommandClass.__proto__ !== Command) {
    console.warn("Bad command", o.command, "resolves to:", CommandClass);
    return;
  }
  let command = new CommandClass(o);
  console.log("Incoming:", command);
  model.applyCommand(command);
}

function send(command) {
  if (!command || (!(command instanceof Command))) {
    throw new Error(`Bad command: ${command}`);
  }
  model.applyCommand(command);
  console.log("Send:", command);
  let j = JSON.stringify(command);
  socket.send(j);
}
