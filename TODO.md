* Make the dangerousSetInnerHTML with tooltip a component
* Change FILES to allow del FILES[path], with a trashcan
* Do something with FILES and subdirectories
* Make FILES["somedir/"] be able to create directories as needed
* Fix file watching
* Make images possible fields
* Create JSON encoding of data
* Create Pickle encoding of data
* Show progress of execution (intermediate work? Just a timer?)
  * Show incremental output
  * Put a counter into loops, so loops can be tracked for progress
    * Start with something simpler like for_reporter(iter)
* Consider https://github.com/JedWatson/react-codemirror for textarea
* Handle empty directories (currently nothing is rendered)
* Use random number as the ID of the server, do full resync if the page isn't setup for the server
* on_open, after sending all events, check actual file content against expected (due to replay) content, and create FileEdits if necessary.
* Markdown support
  * Allow embedding code (that generates things) inside the Markdown
  * Allow embedding fields in the Markdown (that can be read from code)
  * Use https://github.com/benrlodge/react-simplemde-editor and https://simplemde.com/
* Move "objects" that are referrable to a specially-named key, like `{__objects: ["uuid1", "uuid2"]}` – scan deeply for those objects to know what to store/keep.
  * When rendering the renderer should be told if a remote object is alive or dead
* Switch to Semantic UI: https://react.semantic-ui.com/introduction (mostly done)
  * Tabs for something: https://react.semantic-ui.com/modules/tab
  * Sidebar for something: https://react.semantic-ui.com/modules/sidebar
  * Search for navigating items: https://react.semantic-ui.com/modules/search
  * Modal for help: https://react.semantic-ui.com/modules/modal
  * Table for numpy arrays: https://react.semantic-ui.com/collections/table
  * Loader during execution: https://react.semantic-ui.com/elements/loader
  * Maybe labels for variable definitions: https://react.semantic-ui.com/elements/label
