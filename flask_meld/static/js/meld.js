var Meld = (function () {
  var meld = {};  // contains all methods exposed publicly in the meld object
  var socketio = "";
  var messageUrl = "";
  var csrfTokenHeaderName = 'X-CSRFToken';
  var data = {};
  const components = {};
  var _data = null;

  /*
    Initializes the meld object.
    */
  meld.init = function (_messageUrl) {
    messageUrl = _messageUrl;
    meld.socketio = io();

    meld.socketio.on('response', function(responseJson) {
       if (!responseJson) {
         return
       }

       if (responseJson.error) {
         console.error(responseJson.error);
         return
       }

       updateData(responseJson.data);
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

function updateData(newData){
  for (var key in newData) {
    if (_data[key] !== null){
      _data[key] = newData[key];
    }
  }
}

function addModelEventListener(component, el, eventType) {
  el.addEventListener(eventType, (event) => {
    const element = new Element(event.target);

    const action = {
      type: "syncInput",
      payload: {
        name: element.model.name,
        value: element.getValue(),
      },
    };

    sendMessage(component, component.root, component.id, action, function () {
    });
  });
}
/**
 * Encapsulate DOM element attribute for meld-related information.
 */
class Attribute {
  constructor(attribute) {
    this.attribute = attribute;
    this.name = this.attribute.name;
    this.value = this.attribute.value;
    this.isMeld = false;
    this.isModel = false;
    this.isField = false;
    this.isPoll = false;
    this.isLoading = false;
    this.isTarget = false;
    this.isKey = false;
    this.isPK = false;
    this.isError = false;
    this.modifiers = {};
    this.eventType = null;

    this.init();
  }

  /**
   * Init the attribute.
   */
  init() {
    if (this.name.startsWith("meld:")) {
      this.isMeld = true;

      // Use `contains` when there could be modifiers
      if (contains(this.name, ":model")) {
        this.isModel = true;
      } else if (contains(this.name, ":field")) {
        this.isField = true;
      } else if (contains(this.name, ":db")) {
        this.isDb = true;
      } else if (contains(this.name, ":poll")) {
        this.isPoll = true;
      } else if (contains(this.name, ":loading")) {
        this.isLoading = true;
      } else if (contains(this.name, ":target")) {
        this.isTarget = true;
      } else if (this.name === "meld:key") {
        this.isKey = true;
      } else if (this.name === "meld:pk") {
        this.isPK = true;
      } else if (contains(this.name, ":error:")) {
        this.isError = true;
      } else {
        const actionEventType = this.name
          .replace("meld:", "")

        if (
          actionEventType !== "id" &&
          actionEventType !== "name" &&
          actionEventType !== "checksum"
        ) {
          this.eventType = actionEventType;
        }
      }

      let potentialModifiers = this.name;

      if (this.eventType) {
        potentialModifiers = this.eventType;
      }

      // Find modifiers and any potential arguments
      potentialModifiers
        .split(".")
        .slice(1)
        .forEach((modifier) => {
          const modifierArgs = modifier.split("-");
          this.modifiers[modifierArgs[0]] =
            modifierArgs.length > 1 ? modifierArgs[1] : true;

          // Remove any modifier from the event type
          if (this.eventType) {
            this.eventType = this.eventType.replace(`.${modifier}`, "");
          }
        });
    }
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
/**
 * Checks if an object is empty. Useful to check if a dictionary has a value.
 */
function isEmpty(obj) {
  return (
    typeof obj === "undefined" ||
    obj === null ||
    (Object.keys(obj).length === 0 && obj.constructor === Object)
  );
}
/**
 * Checks if an object has a value.
 */
function hasValue(obj) {
  return !isEmpty(obj);
}

/**
 * Encapsulate DOM element for Meld-related information.
 */
class Element {
  constructor(el) {
    this.el = el;
    this.init();
  }

  /**
   * Check if another `Element` is the same as this `Element`.
   * @param {Element} other
   */
  isSame(other) {
    // Use isSameNode (not isEqualNode) because we want to check the nodes reference the same object
    return this.el.isSameNode(other.el);
  }

  /**
   * Gets the value from the element.
   */
  getValue() {
    let { value } = this.el;

    if (this.el.type) {
      if (this.el.type.toLowerCase() === "checkbox") {
        // Handle checkbox
        value = this.el.checked;
      } else if (this.el.type.toLowerCase() === "select-multiple") {
        // Handle multiple select options
        value = [];
        for (let i = 0; i < this.el.selectedOptions.length; i++) {
          value.push(this.el.selectedOptions[i].value);
        }
      }
    }

    return value;
  }
  /**
   * Get the element's next parent that is a unicorn element.
   *
   * Returns `null` if no unicorn element can be found before the root.
   */
  getMeldParent() {
    let parentElement = this.parent;

    while (parentElement && !parentElement.isMeld) {
      parentElement = parentElement.parent;
    }

    return parentElement;
  }

  /**
   * Init the element.
   */
  init() {
    this.id = this.el.id;
    this.isMeld= false;
    this.attributes = [];
    this.parent = null;

    if (this.el.parentElement) {
      this.parent = new Element(this.el.parentElement);
    }

    this.model = {};
    this.poll = {};
    this.loading = {};
    this.actions = [];
    this.db = {};
    this.field = {};
    this.target = null;
    this.key = null;
    this.errors = [];

    if (!this.el.attributes) {
      return;
    }

    for (let i = 0; i < this.el.attributes.length; i++) {
      const attribute = new Attribute(this.el.attributes[i]);
      this.attributes.push(attribute);

      if (attribute.isMeld) {
        this.isMeld= true;
      }

      if (attribute.isModel) {
        this.model.name = attribute.value;
        this.model.eventType = attribute.modifiers.lazy ? "blur" : "input";
        this.model.isLazy = !!attribute.modifiers.lazy;
        this.model.isDefer = !!attribute.modifiers.defer;
        this.model.debounceTime = attribute.modifiers.debounce
          ? parseInt(attribute.modifiers.debounce, 10) || -1
          : -1;
      } else if (attribute.isField) {
        this.field.name = attribute.value;
        this.field.eventType = attribute.modifiers.lazy ? "blur" : "input";
        this.field.isLazy = !!attribute.modifiers.lazy;
        this.field.isDefer = !!attribute.modifiers.defer;
        this.field.debounceTime = attribute.modifiers.debounce
          ? parseInt(attribute.modifiers.debounce, 10) || -1
          : -1;
      } else if (attribute.isDb) {
        this.db.name = attribute.value;
      } else if (attribute.isPK) {
        this.db.pk = attribute.value;
      } else if (attribute.isPoll) {
        this.poll.method = attribute.value ? attribute.value : "refresh";
        this.poll.timing = 2000;

        const pollArgs = attribute.name.split("-").slice(1);

        if (pollArgs.length > 0) {
          this.poll.timing = parseInt(pollArgs[0], 10) || 2000;
        }
      } else if (attribute.isLoading) {
        if (attribute.modifiers.attr) {
          this.loading.attr = attribute.value;
        } else if (attribute.modifiers.class && attribute.modifiers.remove) {
          this.loading.removeClass = attribute.value;
        } else if (attribute.modifiers.class) {
          this.loading.class = attribute.value;
        } else if (attribute.modifiers.remove) {
          this.loading.hide = true;
        } else {
          this.loading.show = true;
        }
      } else if (attribute.isTarget) {
        this.target = attribute.value;
      } else if (attribute.eventType) {
        const action = {};
        action.name = attribute.value;
        action.eventType = attribute.eventType;
        action.isPrevent = false;
        action.isStop = false;

        if (attribute.modifiers) {
          Object.keys(attribute.modifiers).forEach((modifier) => {
            if (modifier === "prevent") {
              action.isPrevent = true;
            } else if (modifier === "stop") {
              action.isStop = true;
            } else {
              // Assume the modifier is a keycode
              print(modifier)
              action.key = modifier;
            }
          });
        }

        this.actions.push(action);
      }

      if (attribute.isKey) {
        this.key = attribute.value;
      }
    }
    }
    }

/**
 * Adds an action event listener to the document for each type of event (e.g. click, keyup, etc).
 * Added at the document level because validation errors would sometimes remove the
 * events when attached directly to the element.
 * @param {Component} component Component that contains the element.
 * @param {string} eventType Event type to listen for.
 */
function addActionEventListener(component, eventType) {
  component.document.addEventListener(eventType, (event) => {
    let targetElement = new Element(event.target);

    // Make sure that the target element is a meld element.
    if (targetElement && !targetElement.isMeld) {
      targetElement = targetElement.getMeldParent();
    }

    if (
      targetElement &&
      targetElement.isMeld &&
      targetElement.actions.length > 0
    ) {
      component.actionEvents[eventType].forEach((actionEvent) => {
        const { action } = actionEvent;
        const { element } = actionEvent;

        if (targetElement.isSame(element)) {
          // Add the value of any child element of the target that is a lazy model to the action queue
          // Handles situations similar to https://github.com/livewire/livewire/issues/528

          component.walker(element.el, (childEl) => {
            const modelElsInTargetScope = component.modelEls.filter((e) =>
              e.el.isSameNode(childEl)
            );

            modelElsInTargetScope.forEach((modelElement) => {
              if (hasValue(modelElement.model) && modelElement.model.isLazy) {
                const actionForQueue = {
                  type: "syncInput",
                  payload: {
                    name: modelElement.model.name,
                    value: modelElement.getValue(),
                  },
                };
                component.actionQueue.push(actionForQueue);
              }
            });

            const dbElsInTargetScope = component.dbEls.filter((e) =>
              e.el.isSameNode(childEl)
            );

            dbElsInTargetScope.forEach((dbElement) => {
              if (hasValue(dbElement.model) && dbElement.model.isLazy) {
                const actionForQueue = {
                  type: "dbInput",
                  payload: {
                    model: dbElement.model.name,
                    db: dbElement.db.name,
                    pk: dbElement.db.pk,
                    fields: {},
                  },
                };
                actionForQueue.payload.fields[
                  dbElement.field.name
                ] = dbElement.getValue();

                component.actionQueue.push(actionForQueue);
              }
            });
          });

          if (action.isPrevent) {
            event.preventDefault();
          }

          if (action.isStop) {
            event.stopPropagation();
          }
          print(action)
          var method = { type: "callMethod", payload: { name: action.name } };
          if (action.key) {
            print(action.key)
            print(event.key.toLowerCase())
            if (action.key === event.key.toLowerCase()) {
              sendMessage(component, this.root, component.id, method, function () {
              })
            }
          } else {
              sendMessage(component, this.root, component.id, method, function () {
              })
          }
        }
      });
    }
  });
}

class Component {
  constructor(args) {
    this.id = args.id;
    this.name = args.name;
    this.messageUrl = args.messageUrl;
    this.csrfTokenHeaderName = args.csrfTokenHeaderName;

    if (contains(this.name, ".")) {
      const names = this.name.split(".");
      this.name = names[names.length - 2];
    }

    this.data = args.data;

    this.document = args.document || document;
    this.walker = args.walker || walk;

    this.root = undefined;
    this.modelEls = [];
    this.keyEls = [];

    this.actionEvents = {};
    this.attachedEventTypes = [];
    this.attachedModelEvents = [];

    this.init();
    this.refreshEventListeners();
  }


  /**
   * Initializes the Component.
   */
  init() {
    this.root = $(`[meld\\:id="${this.id}"]`, this.document);

    if (!this.root) {
      throw Error("No id found");
    }
    var rc = this.root.getAttribute('meld:data');
    var tmp = rc.replace(/[\"{}]/g,"").split(":");
    data[tmp[0]] = tmp[1];
    _data = data;
  }
  refreshEventListeners() {
    this.actionEvents = {};
    this.modelEls = [];
    this.dbEls = [];

    walk(this.root, (el) => {
      if (el.isSameNode(this.root)) {
        // Skip the component root element
        return;
      }

      const element = new Element(el);

      if (element.isMeld) {
        if (
          hasValue(element.field) &&
          (hasValue(element.db) || hasValue(element.model))
        ) {
          if (!this.attachedDbEvents.some((e) => e.isSame(element))) {
            this.attachedDbEvents.push(element);
            addDbEventListener(this, element.el, element.field.eventType);
          }

          if (!this.dbEls.some((e) => e.isSame(element))) {
            this.dbEls.push(element);
          }
        } else if (
          hasValue(element.model) &&
          isEmpty(element.db) &&
          isEmpty(element.field)
        ) {
          if (!this.attachedModelEvents.some((e) => e.isSame(element))) {
            this.attachedModelEvents.push(element);
            addModelEventListener(this, element.el, element.model.eventType);
          }

          if (!this.modelEls.some((e) => e.isSame(element))) {
            this.modelEls.push(element);
          }
        } else if (hasValue(element.loading)) {
          this.loadingEls.push(element);

          // Hide loading elements that are shown when an action happens
          if (element.loading.show) {
            element.hide();
          }
        }

        if (hasValue(element.key)) {
          this.keyEls.push(element);
        }

        element.actions.forEach((action) => {
          if (this.actionEvents[action.eventType]) {
            this.actionEvents[action.eventType].push({ action, element });
          } else {
            this.actionEvents[action.eventType] = [{ action, element }];

            if (
              !this.attachedEventTypes.some((et) => et === action.eventType)
            ) {
              this.attachedEventTypes.push(action.eventType);
              addActionEventListener(this, action.eventType);
            }
          }
        });
      }
    });
    }
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

  sendMessage(componentName, componentRoot, meldId, action, function () {
  });
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
    Handles calling the message endpoint and merging the results into the document.
    */
function sendMessage(component, componentRoot, meldId, action, callback) {
  meld.socketio.emit('message', {'id': meldId, 'action':action, 'componentName': component.name, 'data': data});
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

/*
    Allow python print
    */
function print(msg) {
  var args = [].slice.apply(arguments).slice(1);
  console.log(msg, ...args);
}

return meld;
}());
