import logging
import sqlite3
import sys

from datetime import datetime
from flask import Flask, json, render_template, request, url_for, redirect, flash

DB_CONNECTION_COUNTER = 0


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# Function to get a post using its ID
def get_post(post_id):
    global DB_CONNECTION_COUNTER
    connection = get_db_connection()
    post = connection.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    DB_CONNECTION_COUNTER += 1
    connection.close()
    return post


# Function to calculate the metrics
def calculate_metrics() -> dict:
    connection = get_db_connection()
    post_count = connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    connection.close()
    return {"db_connection_count": DB_CONNECTION_COUNTER, "post_count": post_count}


def get_current_ts() -> str:
    return datetime.strftime(datetime.now(), '%d/%b/%Y %H:%M:%S')


def validate_db_connection() -> bool:
    try:
        connection = get_db_connection()
        connection.execute("SELECT * FROM posts").fetchall()
        connection.close()
    except sqlite3.OperationalError:
        return False
    return True


# Define the Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "your secret key"


# Define the health route of the web application
@app.route("/healthz")
def healthz():
    if not validate_db_connection():
        return app.response_class(response=json.dumps({"result": "Unhealthy"}), status=500, mimetype="application/json")
    else:
        return app.response_class(
            response=json.dumps({"result": "OK - healthy"}), status=200, mimetype="application/json"
        )


# Define the main route of the web application
@app.route("/")
def index():
    try:
        connection = get_db_connection()
        posts = connection.execute("SELECT * FROM posts").fetchall()
        connection.close()
    except sqlite3.OperationalError:
        return app.response_class(response=json.dumps({"result": "DB error"}), status=500, mimetype="application/json")
    return render_template("index.html", posts=posts)


@app.route("/metrics")
def metrics():
    try:
        metrics = calculate_metrics()
    except sqlite3.OperationalError:
        return app.response_class(response=json.dumps({"result": "DB error"}), status=500, mimetype="application/json")
    response = app.response_class(
            response=json.dumps({"status": "success", "code": 0, "data": metrics}),
            status=200,
            mimetype="application/json",
    )
    app.logger.info(f"[{get_current_ts()}] Calculated metrics: {metrics}")
    return response


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route("/<int:post_id>")
def post(post_id):
    try:
        post = get_post(post_id)
    except sqlite3.OperationalError:
        return app.response_class(response=json.dumps({"result": "DB error"}), status=500, mimetype="application/json")
    if post is None:
        app.logger.info(f"[{get_current_ts()}] The requested article #{post_id} does not exist!")
        return render_template("404.html"), 404
    else:
        app.logger.info(f"[{get_current_ts()}] Article \"{post[2]}\" retrieved!")
        return render_template("post.html", post=post)


# Define the About Us page
@app.route("/about")
def about():
    app.logger.info(f"[{get_current_ts()}] The About page is retrieved!")
    return render_template("about.html")


# Define the post creation functionality
@app.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            try:
                connection = get_db_connection()
                connection.execute("INSERT INTO posts (title, content) VALUES (?, ?)", (title, content))
                connection.commit()
                connection.close()
            except sqlite3.OperationalError:
                return app.response_class(
                    response=json.dumps({"result": "DB error"}),
                    status=500,
                    mimetype="application/json",
                )

            app.logger.info(f"[{get_current_ts()}] A new article \"{title}\" is created successfully!")

            return redirect(url_for("index"))

    return render_template("create.html")


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    app.run(host="0.0.0.0", port="3111")
