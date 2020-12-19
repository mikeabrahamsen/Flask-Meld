import { Component } from "./component.js";
import { Element } from "./element.js";
import { Attribute } from "./attribute.js";
import { contains, hasValue, isEmpty, sendMessage, socketio, print } from "./utils.js";

export var Meld = (function () {
  var meld = {};  // contains all methods exposed publicly in the meld object
  var messageUrl = "";
  var csrfTokenHeaderName = 'X-CSRFToken';
  var data = {};
  const components = {};

  /*
    Initializes the meld object.
    */
  meld.init = function (_messageUrl) {
    messageUrl = _messageUrl;

    socketio.on('response', function(responseJson) {
       if (!responseJson) {
         return
       }

       if (responseJson.error) {
         console.error(responseJson.error);
         return
       }

       updateData(components[responseJson.id], responseJson.data);
       var dom = responseJson.dom;

       var morphdomOptions = {
         childrenOnly: false,
         getNodeKey: function (node) {
           // A node's unique identifier. Used to rearrange elements rather than
           // creating and destroying an element that already exists.
           if (node.attributes) {
             var key = node.getAttribute("meld:key") || node.id;

             if (key) {
               return key;
             }
           }
         },
         onBeforeElUpdated: function (fromEl, toEl) {
           // When dealing with DOM nodes, we want isEqualNode, otherwise
           // isSameNode will ALWAYS return false.
           if (fromEl.isEqualNode(toEl)) {
             return false;
           }
         },
       }
      var componentRoot = $('[meld\\:id="' + responseJson.id + '"]');
      morphdom(componentRoot, dom, morphdomOptions);
      components[responseJson.id].refreshEventListeners()
  });

}

function updateData(component, newData){
  for (var key in newData) {
    component.data[key] = newData[key];
  }
}

/**
 * Checks if a string has the search text.
 */
function contains(str, search) {
  if (!str) {
    return false;
  }

  return str.indexOf(search) > -1;
}


/*
    Initializes the component.
    */
meld.componentInit = function (args) {
  const component = new Component(args);
  components[component.id] = component;

};
function toKebabCase(str) {
  if (!str) {
    return "";
  }

  const match = str.match(
    /[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+/g
  );

  if (!match) {
    return str;
  }

  return match.map((x) => x.toLowerCase()).join("-");
}

/*
    Call an action on the specified component.
    */
meld.call = function (componentName, methodName,args) {
  var meldId = args.id;
  var componentName = args.name;
  var componentRoot = $('[meld\\:id="' + meldId + '"]');

  if (!componentRoot) {
    Error("No component found for: ", componentName);
  }

  var meldId = componentRoot.getAttribute('meld:id');

  if (!meldId) {
    Error("No id found");
  }


  var action = { type: "callMethod", payload: { name: methodName, params: args } };
  var modelEls = [];

  walk(componentRoot, (el) => {
    if (el.isSameNode(componentRoot)) {
      // Skip the component root element
      return
    }
  });

  sendMessage(componentName, componentRoot, meldId, action, data);
}

/*
    Get the CSRF token used by Django.
    */
function getCsrfToken() {
  var csrfToken = "";
  var csrfElements = document.getElementsByName('csrfmiddlewaretoken');

  if (csrfElements.length > 0) {
    csrfToken = csrfElements[0].getAttribute('value');
  }

  if (!csrfToken) {
    console.error("CSRF token is missing. Do you need to add {% csrf_token %}?");
  }

  return csrfToken;
}

/*
    Traverse the DOM looking for child elements.
    */
function walk(el, callback) {
  var walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT, null, false);

  while (walker.nextNode()) {
    // TODO: Handle sub-components
    callback(walker.currentNode);
  }
}
/*
    Get a value from an element. Tries to deal with HTML weirdnesses.
    */
function getValue(el) {
  if (!el.type) {
    return
  }
  let value = el.value;

  // Handle checkbox
  if (el.type.toLowerCase() == "checkbox") {
    value = el.checked;
  }

  // Handle multiple select options
  if (el.type.toLowerCase() == "select-multiple") {
    value = [];
    for (var i = 0; i < el.selectedOptions.length; i++) {
      value.push(el.selectedOptions[i].value);
    }
  }

  return value;
}

/*
    A simple shortcut for querySelector that everyone loves.
    */
function $(selector, scope) {
  if (scope == undefined) {
    scope = document;
  }

  return scope.querySelector(selector);
}


/*
    The function is executed the number of times it is called,
    but there is a fixed wait time before each execution.
    From https://medium.com/ghostcoder/debounce-vs-throttle-vs-queue-execution-bcde259768.
    */
const funcQueue = [];
function queue(func, waitTime) {
  let isWaiting;

  const play = () => {
    let params;
    isWaiting = false;

    if (funcQueue.length) {
      params = funcQueue.shift();
      executeFunc(params);
    }
  };

  const executeFunc = (params) => {
    isWaiting = true;
    func(params);
    setTimeout(play, waitTime);
  };

  return (params) => {
    if (isWaiting) {
      funcQueue.push(params);
    } else {
      executeFunc(params);
    }
  };
}

return meld;
}());
