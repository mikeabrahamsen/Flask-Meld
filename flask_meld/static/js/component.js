import {$, walk, hasValue, isEmpty, sendMessage, print, debounce} from "./utils.js";
import { Element } from "./element.js";

export class Component {
  constructor(args) {
    this.id = args.id;
    this.name = args.name;
    this.messageUrl = args.messageUrl;
    this.csrfTokenHeaderName = args.csrfTokenHeaderName;

    if (this.name.includes(".")) {
      const names = this.name.split(".");
      this.name = names[names.length - 2];
    }

    this.data = args.data;

    this.document = args.document || document;
    this.walker = args.walker || walk;

    this.root = undefined;
    this.modelEls = [];
    this.keyEls = [];

    this.actionQueue = [];

    this.actionEvents = {};
    this.attachedEventTypes = [];
    this.attachedModelEvents = [];

    this.init();
    this.refreshEventListeners();
  }

addModelEventListener(component, el, eventType) {
  el.addEventListener(eventType, (event) => {
    const element = new Element(event.target);

    const action = {
      type: "syncInput",
      payload: {
        name: element.model.name,
        value: element.getValue(),
      },
    };

    if (element.model.isDefer) {
        let foundAction = false;

        // Update the existing action with the current value
        component.actionQueue.forEach((a) => {
          if (a.payload.name === element.model.name) {
            a.payload.value = element.getValue();
            foundAction = true;
          }
        });

        // Add the action if not already in the queue
        if (!foundAction) {
          component.actionQueue.push(action);
        }
        return;
    }

    this.actionQueue.push(action);
    this.queueMessage(element.model.debounceTime);
  });
}

/**
 * Adds an action event listener to the document for each type of event (e.g. click, keyup, etc).
 * Added at the document level because validation errors would sometimes remove the
 * events when attached directly to the element.
 * @param {Component} component Component that contains the element.
 * @param {string} eventType Event type to listen for.
 */
addActionEventListener(component, eventType) {
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
          var method = { type: "callMethod", payload: { name: action.name } };

          if (action.key) {
            if (action.key === event.key.toLowerCase()) {
              this.actionQueue.push(method);
            }
          } else {
              this.actionQueue.push(method);
          }

          this.queueMessage(element.model.debounceTime);
        }
      });
    }
  });
}

queueMessage(debounceTime, callback) {
  if (debounceTime === -1) {
    debounce(sendMessage, 250, false)(this, callback);
  } else {
    debounce(sendMessage, debounceTime, false)(this, callback);
  }
}



  /**
   * Initializes the Component.
   */
  init() {
    this.root = $(`[meld\\:id="${this.id}"]`, this.document);

    if (!this.root) {
      throw Error("No id found");
    }
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
            this.addModelEventListener(this, element.el, element.model.eventType);
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
              this.addActionEventListener(this, action.eventType);
            }
          }
        });
      }
    });
    }
}
