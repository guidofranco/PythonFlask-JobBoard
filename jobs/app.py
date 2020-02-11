import datetime
import os

import psycopg2
import psycopg2.extras
from flask import Flask, g, redirect, render_template, request, url_for

DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_USER_PSWD = os.environ["DB_USER_PSWD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]

app = Flask(__name__)

def open_connection():
    connection = getattr(g, '_connection', None)
    if connection is None:
        connection = g._connection = psycopg2.connect(
                                        dbname=DB_NAME, user=DB_USER,
                                        password=DB_USER_PSWD,
                                        host=DB_HOST, port=DB_PORT)
    return connection


def execute_sql(sql, values=(), commit=False, single=False):
    connection = open_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(sql, values)
    if commit is True:
        results = connection.commit()
    else:
        results = cursor.fetchone() if single else cursor.fetchall()
    cursor.close()
    return results


@app.teardown_appcontext
def close_connection(exception):
    connection = getattr(g, '_connection', None)
    if connection is not None:
        connection.close()


# Route to display index.html template
@app.route("/")
@app.route("/jobs")
def jobs():
    jobs = execute_sql("""
            SELECT job.id, job.title, job.description, job.salary, 
            employer.id as employer_id, employer.name as employer_name
            FROM job JOIN employer ON employer.id = job.employer_id
            """)
    return render_template("index.html", jobs=jobs)


@app.route("/job/<job_id>")
def job(job_id):
    job = execute_sql("""
            SELECT job.id, job.title, job.description, job.salary,
            employer.id as employer_id, employer.name as employer_name
            FROM job JOIN employer ON employer.id = job.employer_id
            WHERE job.id = %s
            """,
            [job_id], single=True)
    return render_template("job.html", job=job)

@app.route("/employer/<employer_id>")
def employer(employer_id):
    employer = execute_sql("""
            SELECT * FROM employer WHERE id=%s
            """,
            [employer_id], single=True)
    jobs = execute_sql("""
            SELECT job.id, job.title, job.description, job.salary
            FROM job JOIN employer ON employer.id = job.employer_id
            WHERE employer.id = %s
            """,
            [employer_id])
    reviews = execute_sql("""
            SELECT review, rating, title, date, status
            FROM review JOIN employer ON employer.id = review.employer_id
            WHERE employer.id = %s
            """,
            [employer_id])
    return render_template("employer.html", employer=employer, jobs=jobs, reviews=reviews)

@app.route("/employer/<employer_id>/review", methods=("GET", "POST"))
def review(employer_id):
    if request.method == "POST":
        review = request.form["review"]
        rating = request.form["rating"]
        title = request.form["title"]
        status = request.form["status"]
        date = datetime.datetime.now().strftime("%m/%d/%Y")
        execute_sql("""
            INSERT INTO review (review, rating, title, date, status, employer_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (review, rating, title, date, status, employer_id), commit=True)
        return redirect(url_for("employer", employer_id=employer_id))
    return render_template("review.html", employer_id=employer_id)

if __name__ == '__main__':
    app.run()
