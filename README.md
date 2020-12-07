# Flask-Meld

Meld is a framework for Flask to meld your frontend and backend code. What does
that mean? It means you can enjoy writing dynamic user interfaces in pure Python.

Less context switching.
No need to write javascript.
More fun!

# Initialize Meld in your project

Example of how add Flask-Meld to a Flask application

```py
from flask import Flask, render_template
from flask_meld import Meld

app = Flask(__name__)
app.config['SECRET_KEY'] = 'big!secret'
socketio = app.socketio

meld = Meld()
meld.init_app(app)


@app.route('/')
def index():
    return render_template("base.html")

if __name__ == '__main__':
    socketio.run(app)
```

# Add `{% meld_scripts %}` to your base html template

```html

<!DOCTYPE html>
<html>
    <head>
        <title>Meld Example</title>
    </head>
    <body>
        <div>
        <!-- Add the line below to include the necessary meld scripts-->
        {% meld_scripts %}

        {% block content %}
            <!-- Using a component in your template is easy! -->
            {% meld 'counter' %}
        {% endblock %}
        </div>
        <style>
        </style>
    </body>
</html>
```

# Components

Components are stored in `meld/components` either within your application folder or in the base directory of your project.

Components are simple Python classes. No magic here.

Here is an example of a Counter Component:
```py
# app/meld/components/counter.py

from flask_meld.component import Component


class Counter(Component):
    count = 0

    def add(self):
        self.count = int(self.count) + 1

    def subtract(self):
        self.count = int(self.count) - 1
```

# Templates

Create a component template in `templates/meld/counter.html`. By creating a file
within the `templates/meld` directory just include `{% meld 'counter' %}` where
you want the component to load.

Here is an example for counter:

```html
<!-- templates/meld/counter.html -->
<div>
    <button meld:click="subtract">-</button>
    <input type="text" meld:model="count" readonly></input>
    <button meld:click="add">+</button>
</div>
```
Let's take a look at that template file in more detail.

The buttons use `meld:click` to call the `add` or `subtract` function of the
Counter component.
The input uses `meld:model` to bind the input to the `count` property on the
Counter component.

Pretty simple right? You can use this to create very dynamic user interfaces
using pure Python and HTML. We would love to see what you have built using Meld
so please share!
