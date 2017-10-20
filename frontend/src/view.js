import React from 'react';
import * as ReactDOM from 'react-dom';
import { Button, Container, Dropdown, Menu, Header, Icon, TextArea, Card, Grid, Popup, List, Accordion, Label, Modal, Dimmer, Loader, Segment } from 'semantic-ui-react';
import { model } from './datalayer';
import { updateFile, deleteFile, executeFile } from './script';

class Page extends React.Component {
  render() {
    let filenames = Array.from(this.props.files.keys());
    filenames.sort()
    let files = filenames.map((name, index) => <File key={name} name={name} index={index} {...this.props.files.get(name)} />);
    return <div>
      {this.props.showNavigation ? <Navigate {...this.props} /> : null}
      <PageMenu {...this.props} />
      <Container style={{ marginTop: '7em' }}>
        {files}
        <fieldset>
          <legend>Add a file</legend>
          <form onSubmit={this.onAddFile.bind(this)}>
            <input id="filename" type="text" ref={el => this.filenameElement = el} />
            <button type="submit">Add</button>
          </form>
        </fieldset>
      </Container>

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

}

class PageMenu extends React.Component {

  render() {
    // See https://github.com/Semantic-Org/Semantic-UI-React/blob/master/docs/app/Layouts/FixedMenuLayout.js
    // for some examples
    // https://react.semantic-ui.com/layouts/fixed-menu
    return <Menu fixed='top' inverted>
      <Container>
        <CloudStatus live={this.props.connectionLive} direction={this.props.connectionDirection} />
        <Dropdown item simple text='Dropdown'>
          <Dropdown.Menu>
            <Dropdown.Item>List Item</Dropdown.Item>
            <Dropdown.Item>List Item</Dropdown.Item>
            <Dropdown.Divider />
            <Dropdown.Header>Header Item</Dropdown.Header>
            <Dropdown.Item>
              <i className='dropdown icon' />
              <span className='text'>Submenu</span>
              <Dropdown.Menu>
                <Dropdown.Item>List Item</Dropdown.Item>
                <Dropdown.Item>List Item</Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown.Item>
            <Dropdown.Item>List Item</Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
        <Help trigger={
          <Menu.Item as="a">Shortcuts: Ctrl+?</Menu.Item>
        } />
      </Container>
    </Menu>;
  }

}

class CloudStatus extends React.Component {
  render() {
    let name = "cloud";
    let color = undefined;
    let disabled = false;
    if (!this.props.live) {
      disabled = true;
      color = "red";
    }
    let src = "/img/icons/cloud.svg";
    if (this.props.direction == "up") {
      name = "cloud upload";
    } else if (this.props.direction == "down") {
      name = "cloud download";
    }
    return <Menu.Item header>
      <Icon color={color} name={name} disabled={disabled} />
    </Menu.Item>;
  }
}

class File extends React.Component {
  constructor(props) {
    super(props);
    this.state = {value: this.props.content, collapsed: false};
    this.seenValues = [];
  }

  render() {
    if (!this.state.value && this.state.value !== "") {
      console.error("Dead file:", this.props.name, model.files[this.props.name]);
    }
    let rows = this.state.value.split("\n").length + 1
    return <div ref={baseEl => this.baseEl = baseEl} data-name={this.props.name} data-collapsed={this.state.collapsed ? "1" : null}>
      <Dimmer.Dimmable as={Segment} dimmed={this.props.isExecuting}>
        <Dimmer className="loading" active={this.props.isExecuting}><Loader active /></Dimmer>
        <Card style={{width: "100%", marginBottom: "1em"}}>
          <Card.Content>
            <Card.Header>
              <Grid>
                <Grid.Column floated="left">
                  <code>{this.props.name}</code>
                </Grid.Column>
                <Grid.Column floated="right" width={2}>
                  <Container textAlign="right" style={{whiteSpace: "nowrap"}}>
                    <Button size="mini" onClick={this.onDelete.bind(this)} negative>del</Button>
                    <Button size="mini" onClick={this.onCollapse.bind(this)}>{this.state.collapsed ? '+' : '-'}</Button>
                  </Container>
                </Grid.Column>
              </Grid>
            </Card.Header>
          </Card.Content>
          <Card.Content>
            {this.state.collapsed ? null :
              <TextArea tabIndex={this.props.index + 1} className="mousetrap" autoHeight rows={4} style={{width: "100%"}} onFocus={this.onFocus.bind(this)} defaultValue={this.state.value} onChange={this.onChange.bind(this)} onKeyDown={this.onKeyDown.bind(this)}></TextArea>
            }
            <Output content={this.state.value} output={this.props.output} analysis={this.props.analysis} />
          </Card.Content>
        </Card>
      </Dimmer.Dimmable>
    </div>;
  }

  get textarea() {
    return this.baseEl && this.baseEl.querySelector("textarea");
  }

  componentWillReceiveProps(nextProps) {
    // seenValues is a really hacky way to avoid some overwrite problems
    // something about the order and flow of change events should instead be fixed
    if (!this.textarea) {
      console.log("Huh, no textarea");
      return;
    }
    if (nextProps.content != this.textarea.value && !this.seenValues.includes(this.textarea.value)) {
      let selectionStart = this.textarea.selectionStart;
      let selectionEnd = this.textarea.selectionEnd;
      this.textarea.value = nextProps.content;
      this.textarea.selectionStart = selectionStart;
      this.textarea.selectionEnd = selectionEnd;
    }
    this.setState({value: nextProps.content});
  }

  onChange(event) {
    let target = event.target;
    this.setState({value: target.value});
    while (this.seenValues.length > 10) {
      this.seenValues.shift();
    }
    this.seenValues.push(target.value)
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
      let subexpressions = !!event.ctrlKey;
      event.preventDefault();
      executeFile(this.props.name, subexpressions);
      return false;
    }
  }

  refreshFocus() {
    if (!model.showNavigation && model.focusName == this.props.name && !this.state.collapsed) {
      this.textarea && this.textarea.focus();
    }
  }

  refreshSelection() {
    if (this.selectionStart !== undefined) {
      console.log("reset selection", this.selectionStart, this.selectionEnd);
      this.textarea.selectionStart = this.selectionStart;
      this.textarea.selectionEnd = this.selectionEnd;
    }
  }

  componentDidMount() {
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
    this.refreshFocus();
    this.refreshSelection();
  }

  componentWillUnmount() {
    this.selectionStart = this.textarea.selectionStart;
    this.selectionEnd = this.textarea.selectionEnd;
  }
}

class Output extends React.Component {
  render() {
    let defines = null;
    if (this.props.output && this.props.output.defines && Object.keys(this.props.output.defines).length) {
      defines = [];
      for (let name in this.props.output.defines) {
        defines.push(
          <List.Item key={name}>
            <VariableDefinition name={name} {...this.props.output.defines[name]} />
          </List.Item>
        );
      }
      defines = <div>
        Defines:
        <List>
          {defines}
        </List>
       </div>;
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
    if (this.props.output && this.props.output.emitted && this.props.output.emitted.length) {
      output = this.renderEmitted(this.props.output.emitted);
    } else if (this.props.output && this.props.output.output) {
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

  renderEmitted(emitted) {
    let items = [];
    for (let i=0; i<emitted.length; i++) {
      let item = emitted[i];
      items.push(this.renderEmittedItem(item, i));
    }
    return <div>
      {items}
    </div>
  }

  renderEmittedItem(item, index) {
    return renderRemoteItem(item, index);
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

}

class VariableDefinition extends React.Component {
  render() {
    let expr = this.props.json;
    if (this.props.name === expr.name) {
      return renderRemoteItem(expr);
    } else {
      return <span><code>{this.props.name}=</code>{renderRemoteItem(expr)}</span>;
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

class Help extends React.Component {
  render() {
    return <Modal trigger={this.props.trigger}>
      <Modal.Header>
        Keyboard Shortcuts
      </Modal.Header>
      <Modal.Content>
        <table className="table">
          <tbody>
            <tr>
              <td>Shift + Enter</td>
              <td>Execute current cell</td>
            </tr>
            <tr>
              <td>Shift + Ctrl + Enter</td>
              <td>Execute current cell, tracking subexpressions</td>
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
      </Modal.Content>
    </Modal>;
  }
}

function renderRemoteItem(item, key, extraProps) {
  if (!item) {
    let exc = new Error("renderRemoteItem got a null item");
    console.error("renderRemoteItem got a null item", exc);
    return <Accordion>
      <Accordion.Title>
        <Label color="red" icon="warning sign">null item</Label>
      </Accordion.Title>
      <Accordion.Content>
        <pre>{exc.stack}</pre>
      </Accordion.Content>
    </Accordion>;
  }
  extraProps = extraProps || {};
  let type = item.type;
  let Factory = Factories[type] || GenericFactory;
  return <Factory key={key} {...item} {...extraProps} />;
}

class Folded extends React.Component {
  constructor() {
    super();
    this.state = {active: false};
  }

  render() {
    let className = this.props.className || "";
    if (this.props.inline) {
      className += " inline";
    }
    return <Accordion styled className={className}>
      <Accordion.Title onClick={this.toggleAccordion.bind(this)} active={this.state.active}>
        <Icon name="dropdown" />
        {this.props.title}
      </Accordion.Title>
      <Accordion.Content active={this.state.active}>
        {this.props.children}
      </Accordion.Content>
    </Accordion>;
  }

  toggleAccordion() {
    this.setState({active: !this.state.active});
  }
}

const Factories = {};

class GenericFactory extends React.Component {
  render() {
    return <pre>
      {JSON.stringify(this.props, null, '  ')}
    </pre>;
  }
}

Factories.plain_repr = class plain_repr extends React.Component {
  render() {
    return <code>{this.props.repr}</code>;
  }
};

Factories.plain_str = class plain_str extends React.Component {
  render() {
    return <code>{this.props.str}</code>;
  }
};

Factories.str = class str extends React.Component {
  render() {
    let s = JSON.stringify(this.props.str);
    if (s.length > 100) {
      let longS = '"""' + s.substr(1, s.length - 2) + '"""';
      longS = longS.replace(/\\n/g, "\n");
      let title = <span><code>{s.substr(0, 40)}</code>...<code>{s.substr(s.length-20)}</code></span>;
      return <Folded className="inline" title={title}>
        <pre style={{overflowWrap: "break-word", whiteSpace: "normal"}}>{longS}</pre>
      </Folded>;
    }
    return <code>{s}</code>;
  }
};

Factories.explicit_html = class explicit_html extends React.Component {
  render() {
    return <div dangerouslySetInnerHTML={{__html: this.props.html}} />;
  }
};

Factories.FunctionType = class FunctionType extends React.Component {
  render() {
    return <code>{this.props.name}()</code>;
  }
};

Factories["class"] = class PythonClass extends React.Component {
  render() {
    return <code>class {this.props.name}</code>;
  }
};

Factories.tuple = Factories.list = class list_tuple extends React.Component {
  render() {
    let parts = [];
    if (this.props.type == "tuple") {
      parts.push(<code key="start">(</code>);
    } else {
      parts.push(<code key="start">[</code>);
    }
    for (let i=0; i<this.props.content.length; i++) {
      let item = this.props.contents[i];
      parts.push(renderRemoteItem(item, i));
    }
    if (this.props.type == "tuple") {
      if (this.props.content.length === 1) {
        parts.push(<code key="end">,)</code>);
      } else {
        parts.push(<code key="end">)</code>);
      }
    } else {
      parts.push(<code key="end">]</code>);
    }
    return <div>{parts}</div>;
  }
};

Factories.print_expr = class print_expr extends React.Component {
  render() {
    return <dl>
      <dt><code>{this.props.expr_string}</code></dt>
      <dd>{renderRemoteItem(this.props.expr_value)}</dd>
    </dl>;
  }
};

Factories.print = class print extends React.Component {
  render() {
    let parts = [];
    for (let i=0; i < this.props.parts.length; i++) {
      let item = this.props.parts[i];
      if (item.type === "str") {
        parts.push(item.str);
      } else {
        parts.push(renderRemoteItem(item, i));
      }
    }
    return <div>
      {parts}
    </div>;
  }
};

Factories.dump = class dump extends React.Component {
  render() {
    return <pre>{this.props.dump}</pre>;
  }
};

Factories.image = class image extends React.Component {
  render() {
    return <img style={{width: "180px", height: "auto"}} src={this.props.url} />;
  }
};

Factories.filename = class filename extends React.Component {
  render() {
    let icon = this.props.icon || "file outline";
    let filename = this.props.filename;
    if (this.props.base && filename.startsWith(this.props.base)) {
      filename = filename.substr(this.props.base.length);
      while (filename.charAt(0) == "/") {
        filename = filename.substr(1);
      }
    }
    let inner = <span>
      <Icon name={icon} />
      <code>{filename}</code>
    </span>;
    if (this.props.embedded) {
      return <Popup trigger={inner}>
        {renderRemoteItem(this.props.embedded)}
      </Popup>;
    }
    return inner;
  }
};

Factories.FilesDict = class FilesDict extends React.Component {
  render() {
    return <div>
      <span style={{marginRight: "1em"}}>
        Files in <code>{this.props.base}</code>:
      </span>
      <List horizontal relaxed>
        {this.props.files.map(
          (item, index) => <List.Item key={index}>{renderRemoteItem(item, null, {base: this.props.base})}</List.Item>
        )}
      </List>
    </div>;
  }
};

export function renderPage() {
  let body = <Page {...model} />;
  ReactDOM.render(body, document.getElementById("root"));
};

window.renderPage = renderPage;

console.log("finished loading view.jsx");
