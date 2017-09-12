class Page extends React.Component {
  render() {
    let filenames = Array.from(this.props.files.keys());
    filenames.sort()
    let files = filenames.map((name, index) => <File key={name} name={name} index={index} {...this.props.files.get(name)} />);
    return <div className="container">
      {this.props.showHelp ? <Help /> : null}
      {this.props.showNavigation ? <Navigate {...this.props} /> : null}
      <nav className="navbar navbar-inverse bg-inverse fixed-top">
        <span onClick={this.onShowHelp.bind(this)} className="navbar-text">Shortcuts: Ctrl+?</span>
      </nav>

      <div className="container" style={{paddingTop: "50px"}}>
        {files}
        <fieldset>
          <legend>Add a file</legend>
          <form onSubmit={this.onAddFile.bind(this)}>
            <input id="filename" type="text" ref={el => this.filenameElement = el} />
            <button type="submit">Add</button>
          </form>
        </fieldset>
      </div>

      <div style={{height: "30em"}}>

      </div>
    </div>;
  }

  onAddFile(event) {
    event.preventDefault();
    let filename = this.filenameElement.value;
    this.filenameElement.value = '';
    updateFile(filename, '');
    return false;
  }

  onShowHelp() {
    model.showHelp = !model.showHelp;
    render();
  }
}

class File extends React.Component {
  constructor(props) {
    super(props);
    this.state = {value: this.props.content, collapsed: false};
  }

  render() {
    if (!this.state.value && this.state.value !== "") {
      console.error("Dead file:", this.props.name, model.files[this.props.name]);
    }
    let rows = this.state.value.split("\n").length + 1
    return <div className={`file card ${this.props.output ? 'with-output' : ''}`} ref={baseEl => this.baseEl = baseEl} data-name={this.props.name} data-collapsed={this.state.collapsed ? "1" : null}>
      <div className="card-header">
        <code>{this.props.name}</code>
        <div className="btn-group btn-group-sm" role="group">
          <button type="button" className="btn btn-danger" onClick={this.onDelete.bind(this)}>del</button>
          <button type="button" className="btn btn-secondary" style={{width: "2em"}} onClick={this.onCollapse.bind(this)}>{this.state.collapsed ? '+' : '-'}</button>
        </div>
      </div>
      <div className="card-body">
        {this.state.collapsed ? null :
          <textarea ref={textareaEl => this.textareaEl = textareaEl} tabIndex={this.props.index + 1} className="mousetrap" style={{height: (rows * 1.1) + "em"}} onFocus={this.onFocus.bind(this)} defaultValue={this.state.value} onChange={this.onChange.bind(this)} onKeyDown={this.onKeyDown.bind(this)}></textarea>
        }
        <Output content={this.state.value} output={this.props.output} analysis={this.props.analysis} />
      </div>
    </div>;
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.content != this.textareaEl.value) {
      let selectionStart = this.textareaEl.selectionStart;
      let selectionEnd = this.textareaEl.selectionEnd;
      this.textareaEl.value = nextProps.content;
      this.textareaEl.selectionStart = selectionStart;
      this.textareaEl.selectionEnd = selectionEnd;
    }
    this.setState({value: nextProps.content});
  }

  onChange(event) {
    let target = event.target;
    this.setState({value: target.value});
    if (!this.updateTimeout) {
      this.updateTimeout = setTimeout(() => {
        updateFile(this.props.name, target.value);
        this.updateTimeout = null;
      }, 300);
    }
  }

  onFocus() {
    model.focusName = this.props.name;
  }

  onDelete(event) {
    if (window.confirm("Really delete?")) {
      this.setState({value: 'deleting...'});
      deleteFile(this.props.name);
    }
  }

  onCollapse() {
    this.setState({collapsed: !this.state.collapsed});
  }

  onKeyDown(event) {
    if ((event.key || event.code) == "Enter" && event.shiftKey) {
      event.preventDefault();
      executeFile(this.props.name);
      return false;
    }
  }

  refreshHeight() {
    if (this.textareaEl) {
      let idealHeight = this.textareaEl.scrollHeight;
      this.textareaEl.style.height = idealHeight + "px";
    }
  }

  refreshFocus() {
    if (!model.showNavigation && model.focusName == this.props.name && !this.state.collapsed) {
      this.textareaEl.focus();
    }
  }

  refreshSelection() {
    if (this.selectionStart !== undefined) {
      console.log("reset selection", this.selectionStart, this.selectionEnd);
      this.textareaEl.selectionStart = this.selectionStart;
      this.textareaEl.selectionEnd = this.selectionEnd;
    }
  }

  componentDidMount() {
    this.refreshHeight();
    this.refreshFocus();
    this.refreshSelection();
    this.baseEl.addEventListener("collapse", () => {
      this.onCollapse();
    }, false);
    this.baseEl.addEventListener("collapse-down", () => {
      this.setState({collapsed: true});
    }, false);
  }

  componentDidUpdate() {
    this.refreshHeight();
    this.refreshFocus();
    this.refreshSelection();
  }

  componentWillUnmount() {
    this.selectionStart = this.textareaEl.selectionStart;
    this.selectionEnd = this.textareaEl.selectionEnd;
  }
}

class Output extends React.Component {
  render() {
    let defines = null;
    if (this.props.output && this.props.output.defines && Object.keys(this.props.output.defines).length) {
      defines = [];
      for (let name in this.props.output.defines) {
        defines.push(
          <li key={name}>
            <VariableDefinition name={name} {...this.props.output.defines[name]} />
          </li>
        );
      }
      defines = <div>Defines: <ul className="varlist">{defines}</ul></div>;
    }
    let imports = null;
    let used = null;
    if (this.props.analysis) {
      imports = this.makeList("Imports:", this.props.analysis.imports);
      used = this.makeList("Uses:", this.props.analysis.variables_used);
      // Not very interesting:
      // let set = this.makeList("Sets:", this.props.output.variables_set);
    }
    let output = null
    if (this.props.output && this.props.output.output) {
      output = <div className="output" ref={outputEl => this.outputEl = outputEl} dangerouslySetInnerHTML={{__html: this.props.output.output}}></div>;
      if (this.props.output.content != this.props.content) {
        output = <div>
          <span className="badge badge-warning">stale</span>
          {output}
        </div>;
      }
    }
    return <div>
      {imports}
      {used}
      {defines}
      {output}
    </div>;
  }

  makeList(title, items) {
    if (!items || !items.length) {
      return null;
    }
    let lis = [];
    for (let name of items) {
      lis.push(<li key={name}><code>{name}</code></li>);
    }
    return <div>
      {title} <ul className="varlist">{lis}</ul>
    </div>;
  }

  componentDidMount() {
    $(this.outputEl).find('[data-toggle="tooltip"]').tooltip();
  }

  componentDidUpdate() {
    this.componentDidMount();
  }

}

class VariableDefinition extends React.Component {
  render() {
    let r = <span dangerouslySetInnerHTML={{__html: this.props.repr}}></span>;
    if (this.props.self_naming) {
      return r;
    } else {
      return <span><code>{this.props.name}=</code>{r}</span>;
    }
  }
}

class Navigate extends React.Component {
  constructor(props) {
    super(props);
    this.state = {value: "", index: 0};
  }

  render() {
    let options = [];
    let value = this.state.value;
    let selectedName = null;
    let filenames = Object.keys(this.props.files);
    filenames.sort();
    if (value) {
      filenames = filenames.filter(f => f.includes(value));
    }
    let selectedIndex = this.state.index >= filenames.length ? filenames.length - 1 : this.state.index;
    for (let i=0; i<filenames.length; i++) {
      let name = filenames[i];
      let className = "list-group-item";
      if (i == this.state.index) {
        className += " active";
        selectedName = name;
      }
      options.push(<li className={className} key={name}>{name}</li>);
    }
    if (!options.length) {
      options.push(<li className="list-group-item" key="nothing">Nothing</li>);
    }
    return <Modal title="Navigate" onClose={this.onClose.bind(this)}>
      <input ref={inputEl => this.inputEl = inputEl} value={value} onChange={this.onChange.bind(this)} onKeyDown={this.onKeyDown.bind(this)} data-selected={selectedName} style={{width: "100%"}} />
      <ul className="list-group">
        {options}
      </ul>
    </Modal>;
  }

  onChange(event) {
    let target = event.target;
    this.setState({value: target.value});
  }

  onKeyDown(event) {
    if (event.key == "ArrowUp") {
      let newIndex = this.state.index - 1;
      newIndex = newIndex < 0 ? 0 : newIndex;
      this.setState({index: newIndex});
      event.preventDefault();
    } else if (event.key == "ArrowDown") {
      this.setState({index: this.state.index + 1});
      event.preventDefault();
    } else if (event.key == "Enter") {
      let name = event.target.getAttribute("data-selected");
      if (name) {
        model.focusName = name;
        this.onClose();
      }
      event.preventDefault();
    }
  }

  componentDidMount() {
    this.inputEl.focus();
  }

  onClose() {
    model.showNavigation = false;
    render();
  }
}

class Modal extends React.Component {
  render() {
    return <div className="modal" ref={modalEl => this.modalEl = modalEl}>
      <div className="modal-dialog" role="document">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">{this.props.title}</h5>
            <button type="button" className="close" onClick={this.props.onClose.bind(this)} aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div className="modal-body">
            {this.props.children}
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-primary" onClick={this.props.onClose.bind(this)}>Close</button>
          </div>
        </div>
      </div>
    </div>;
  }

  componentDidMount() {
    $(this.modalEl).modal("show");
    $(this.modalEl).on("hidden.bs.modal", () => {
      this.props.onClose();
    });
  }

  componentWillUnmount() {
    $(this.modalEl).modal("hide");
  }
}

class Help extends React.Component {
  render() {
    return <Modal title="Keyboard Shortcuts" onClose={this.onClose.bind(this)}>
      <table className="table">
        <tbody>
          <tr>
            <td>Shift + Enter</td>
            <td>Execute current cell</td>
          </tr>
          <tr>
            <td>Command/Ctrl + Shift + A</td>
            <td>Execute all cells</td>
          </tr>
          <tr>
            <td>Ctrl + T</td>
            <td>File/cell browser</td>
          </tr>
          <tr>
            <td>Ctrl + E</td>
            <td>Expand/collapse current cell</td>
          </tr>
          <tr>
            <td>Ctrl + Shift + E</td>
            <td>Expand/collapse all cells</td>
          </tr>
        </tbody>
      </table>
    </Modal>;
  }

  onClose() {
    model.showHelp = false;
    render();
  }
}

function render() {
  let body = <Page {...model} />;
  ReactDOM.render(body, document.getElementById("react-container"));
}

console.log("finished loading view.jsx");
