from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

def save_tasks(tasks):
    with open(DATA_FILE, "w") as file:
        json.dump(tasks, file, indent=4)

@app.route("/")
def index():
    tasks = load_tasks()
    return render_template("index.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add():
    title = request.form["title"]
    priority = request.form["priority"]
    status = request.form["status"]
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if title.strip():
        tasks = load_tasks()
        tasks.append({
            "title": title,
            "priority": priority,
            "status": status,
            "date": date
        })
        save_tasks(tasks)
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>")
def delete(task_id):
    tasks = load_tasks()
    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)
        save_tasks(tasks)
    return redirect(url_for("index"))

@app.route("/toggle_status/<int:task_id>")
def toggle_status(task_id):
    tasks = load_tasks()
    if 0 <= task_id < len(tasks):
        if tasks[task_id]["status"] == "Done":
            tasks[task_id]["status"] = "Pending"
        else:
            tasks[task_id]["status"] = "Done"
        save_tasks(tasks)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
