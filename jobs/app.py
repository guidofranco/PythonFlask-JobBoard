from flask import Flask, render_template

app = Flask(__name__)

# Route to display index.html template
@app.route("/")
@app.route("/jobs")
def jobs():
    return render_template("index.html")