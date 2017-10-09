* Make the dangerousSetInnerHTML with tooltip a component
* Change FILES to allow del FILES[path], with a trashcan
* Do something with FILES and subdirectories
* Make FILES["somedir/"] be able to create directories as needed
* Fix file watching
* Make images possible fields
* Create JSON encoding of data
* Create Pickle encoding of data
* Show when a file is in the process of being executed
* Show progress of execution (intermediate work? Just a timer?)
  * Show incremental output
  * Put a counter into loops, so loops can be tracked for progress
    * Start with something simpler like for_reporter(iter)
* Consider https://github.com/buildo/react-autosize-textarea for textarea
* Consider https://github.com/JedWatson/react-codemirror for textarea
* Switch to a builder (webpack I guess)
* Handle empty directories (currently nothing is rendered)
* Use random number as the ID of the server, do full resync if the page isn't setup for the server
* Allow draggable resizing of images
* Markdown support
  * Allow embedding code (that generates things) inside the Markdown
  * Allow embedding fields in the Markdown (that can be read from code)
  * Use https://github.com/benrlodge/react-simplemde-editor and https://simplemde.com/
* Get rid of print_expr where the name of the value matches the object:
  * Classes referred to by their base name
  * Methods referred to as attribute access using their normal name
  * Never show our builtins
  * Never show any normally named builtins
