from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from neo4j import GraphDatabase
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Neo4j connection
uri = "neo4j+s://bc1b6ebb.databases.neo4j.io"
username = "neo4j"
password = "ZpR7RK9Tl900OW4QHGrj0bfElE1cEDKSqDY4484DNJM"
driver = GraphDatabase.driver(uri, auth=(username, password))

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ----------------- User Class -----------------
class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

# ----------------- Neo4j User Functions -----------------
def find_user_by_username(username):
    with driver.session() as session:
        result = session.run("MATCH (u:User {username: $username}) RETURN u, id(u) AS id", username=username)
        record = result.single()
        if record:
            user = record["u"]
            return User(user_id=record["id"], username=user["username"])
        return None

def validate_user(username, password):
    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {username: $username, password: $password}) RETURN u, id(u) AS id",
            username=username, password=password
        )
        record = result.single()
        if record:
            return User(user_id=record["id"], username=username)
        return None

def create_user(username, password):
    with driver.session() as session:
        session.run("CREATE (u:User {username: $username, password: $password})",
                    username=username, password=password)

# ----------------- Neo4j Task Functions -----------------
def get_tasks_by_user(user_id):
    with driver.session() as session:
        user_result = session.run(
            "MATCH (u:User) WHERE ID(u) = $user_id RETURN u.username AS username",
            user_id=int(user_id)
        ).single()

        if not user_result:
            return []

        username = user_result["username"]

        result = session.run("""
            MATCH (u:User {username: $username})-[:OWNS]->(t:Task)
            RETURN t, ID(t) AS id ORDER BY t.date DESC
        """, username=username)

        tasks = []
        for record in result:
            task_node = record["t"]
            task_data = dict(task_node)  # Convert Node to dictionary
            task_data["id"] = record["id"]  # Add the task ID
            tasks.append(task_data)

        return tasks

def add_task(user_id, title, priority, status, date):
    with driver.session() as session:
        session.run("""
            MATCH (u:User) WHERE ID(u) = $user_id
            CREATE (t:Task {title: $title, priority: $priority, status: $status, date: $date})
            CREATE (u)-[:OWNS]->(t)
        """, user_id=int(user_id), title=title, priority=priority, status=status, date=date)

def delete_task(user_id, task_id):
    with driver.session() as session:
        session.run("""
            MATCH (u:User)-[:OWNS]->(t:Task)
            WHERE ID(u) = $user_id AND ID(t) = $task_id
            DETACH DELETE t
        """, user_id=int(user_id), task_id=int(task_id))

def toggle_task_status(user_id, task_id):
    with driver.session() as session:
        session.run("""
            MATCH (u:User)-[:OWNS]->(t:Task)
            WHERE ID(u) = $user_id AND ID(t) = $task_id
            SET t.status = CASE t.status
                WHEN 'Done' THEN 'Pending'
                ELSE 'Done'
            END
        """, user_id=int(user_id), task_id=int(task_id))

# ----------------- Flask-Login -----------------
@login_manager.user_loader
def load_user(user_id):
    with driver.session() as session:
        result = session.run("MATCH (u:User) WHERE ID(u) = $id RETURN u", id=int(user_id))
        record = result.single()
        if record:
            user = record["u"]
            return User(user_id=user_id, username=user["username"])
        return None

# ----------------- Routes -----------------
@app.route("/")
@login_required
def index():
    tasks = get_tasks_by_user(current_user.id)
    return render_template("index.html", tasks=tasks, username=current_user.username)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = validate_user(request.form["username"], request.form["password"])
        if user:
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if find_user_by_username(request.form["username"]):
            flash("Username already exists.")
        else:
            create_user(request.form["username"], request.form["password"])
            flash("Registered successfully! Please log in.")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout_view():
    logout_user()
    return redirect(url_for("login"))

@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form["title"]
    priority = request.form["priority"]
    status = request.form["status"]
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if title.strip():
        add_task(current_user.id, title, priority, status, date)
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>")
@login_required
def delete(task_id):
    delete_task(current_user.id, task_id)
    return redirect(url_for("index"))

@app.route("/toggle_status/<int:task_id>")
@login_required
def toggle_status(task_id):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {username: $username})-[:OWNS]->(t:Task)
            WHERE ID(t) = $task_id
            RETURN t.status AS status
        """, username=current_user.username, task_id=int(task_id)).single()

        if result:
            current_status = result["status"]

            if current_status == "Pending":
                new_status = "In Progress"
            elif current_status == "In Progress":
                new_status = "Done"
            else:
                return redirect(url_for("index"))

            session.run("""
                MATCH (u:User {username: $username})-[:OWNS]->(t:Task)
                WHERE ID(t) = $task_id
                SET t.status = $new_status
            """, username=current_user.username, task_id=int(task_id), new_status=new_status)

    return redirect(url_for("index"))

# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(debug=True)
