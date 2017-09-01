let AllCommands = {};

class Model {
  constructor() {
    this.files = new Map();
    this.showHelp = false;
    this.showNavigation = false;
  }

  applyCommand(command) {
    command.applyToModel(this);
    this.render();
  }

  render() {
    render();
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
    if (!this.external_edit) {
      return;
    }
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
  }
};
