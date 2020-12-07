export var socketio = io();
/*
    Handles calling the message endpoint and merging the results into the document.
    */
export function sendMessage(component, componentRoot, meldId, action, data) {
  socketio.emit('message', {'id': meldId, 'action':action, 'componentName': component.name, 'data': data});
}

/*
Traverse the DOM looking for child elements.
*/
export function walk(el, callback) {
  var walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT, null, false);

  while (walker.nextNode()) {
    // TODO: Handle sub-components
    callback(walker.currentNode);
  }
}

/*
A simple shortcut for querySelector that everyone loves.
*/
export function $(selector, scope) {
  if (scope == undefined) {
    scope = document;
  }

  return scope.querySelector(selector);
}

/**
 * Checks if a string has the search text.
 */
export function contains(str, search) {
  if (!str) {
    return false;
  }

  return str.indexOf(search) > -1;
}

/**
 * Checks if an object has a value.
 */
export function hasValue(obj) {
  return !isEmpty(obj);
}

/**
 * Checks if an object is empty. Useful to check if a dictionary has a value.
 */
export function isEmpty(obj) {
  return (
    typeof obj === "undefined" ||
    obj === null ||
    (Object.keys(obj).length === 0 && obj.constructor === Object)
  );
}

/*
    Allow python print
    */
export function print(msg) {
  var args = [].slice.apply(arguments).slice(1);
  console.log(msg, ...args);
}

