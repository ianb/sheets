let AllCommands = {};

class Model {
  constructor() {
    this.files = new Map();
    this.showHelp = false;
    this.showNavigation = false;
    this.connectionLive = false;
    this.connectionDirection = null;
    this._connectionTimeout = null;
  }

  applyCommand(command) {
    command.applyToModel(this);
    this.render();
  }

  render() {
    if (window.render) {
      render();
    }
  }

  setConnectionDirection(dir) {
    if (dir != "up" && dir != "down" && dir !== null) {
      throw new Error(`Bad direction: ${dir}`);
    }
    this.connectionDirection = dir;
    if (this._connectionTimeout) {
      clearTimeout(this._connectionTimeout);
      this._connectionTimeout = null;
    }
    if (dir) {
      this._connectionTimeout = setTimeout(() => {
        this.setConnectionDirection(null);
        this.render();
      }, 1000);
    }
  }
}

class Command {

  toJSON() {
    let data = {};
    for (let attr in this) {
      data[attr] = this[attr];
    }
    data.command = this.constructor.name;
    return data;
  }

  applyToModel(model) {
  }
}

const FileEdit = AllCommands.FileEdit = class FileEdit extends Command {
  constructor(options) {
    super()
    this.filename = options.filename;
    this.content = options.content;
    this.external_edit = !!options.external_edit;
  }

  applyToModel(model) {
    /*
    Pretty sure this concept is just wrong, but especially with replay:
    if (!this.external_edit) {
      return;
    }
    */
    if (!model.files.get(this.filename)) {
      model.files.set(this.filename, {});
    }
    let f = model.files.get(this.filename);
    f.content = this.content;
    f.external_edit = this.external_edit;
  }
};

const FileDelete = AllCommands.FileDelete = class FileDelete extends Command {
  constructor(options) {
    super()
    this.filename = options.filename;
    this.external_edit = !!options.external_edit;
  }

  applyToModel(model) {
    model.files.delete(this.filename);
  }
};

const ExecutionRequest = AllCommands.ExecutionRequest = class ExecutionRequest extends Command {
  constructor(options) {
    super()
    this.filename = options.filename;
    this.content = options.content;
    this.subexpressions = options.subexpressions;
  }

  applyToModel(model) {
    if (!model.files.get(this.filename)) {
      model.files.set(this.filename, {});
    }
    let f = model.files.get(this.filename);
    f.isExecuting = true;
  }
};

const Analysis = AllCommands.Analysis = class Analysis extends Command {
  constructor(options) {
    super()
    this.filename = options.filename;
    this.content = options.content;
    this.properties = options.properties;
  }
  applyToModel(model) {
    if (!model.files.get(this.filename)) {
      console.warn("Got analysis for file that doesn't exist:", this.filename)
      return;
    }
    let f = model.files.get(this.filename);
    if (!f) {
      return;
    }
    if (!f.analysis) {
      f.analysis = {};
    }
    f.analysis.content = this.content;
    f.analysis.properties = this.properties;
  }
};

const Execution = AllCommands.Execution = class Execution extends Command {
  constructor(options) {
    super()
    this.filename = options.filename;
    this.content = options.content;
    this.output = options.output;
    this.defines = options.defines;
    this.start_time = options.start_time;
    this.end_time = options.end_time;
    this.exec_time = options.exec_time;
    this.with_subexpressions = options.with_subexpressions
  }
  applyToModel(model) {
    let f = model.files.get(this.filename);
    if (!f) {
      return;
    }
    f.output = {
      content: this.content,
      output: this.output,
      defines: this.defines,
    };
    f.isExecuting = false;
  }
};
