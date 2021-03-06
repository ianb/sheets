export let AllCommands = {};

export class Model {
  constructor() {
    this.files = new Map();
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
    if (window.renderPage) {
      renderPage();
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

export const model = new Model();

// Expose this to the console:
window.model = model;

export class Command {

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

export const FileEdit = AllCommands.FileEdit = class FileEdit extends Command {
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

export const FileDelete = AllCommands.FileDelete = class FileDelete extends Command {
  constructor(options) {
    super()
    this.filename = options.filename;
    this.external_edit = !!options.external_edit;
  }

  applyToModel(model) {
    model.files.delete(this.filename);
  }
};

export const ExecutionRequest = AllCommands.ExecutionRequest = class ExecutionRequest extends Command {
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

export const Analysis = AllCommands.Analysis = class Analysis extends Command {
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

export const Execution = AllCommands.Execution = class Execution extends Command {
  constructor(options) {
    super()
    this.filename = options.filename;
    this.content = options.content;
    this.emitted = options.emitted;
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
      emitted: this.emitted,
      defines: this.defines,
    };
    f.isExecuting = false;
  }
};
