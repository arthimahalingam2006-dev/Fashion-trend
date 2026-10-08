from flask import Flask, request, jsonify, render_template, redirect, session, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__, template_folder="Template")
app.secret_key = "fashion_trend_secret_key_2026"

CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "fashion_trend.db")
IMAGE_FOLDER = os.path.join(BASE_DIR, "images")


# =========================================================
# DATABASE
# =========================================================

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin():
    return (
        "user_id" in session
        and session.get("role") == "admin"
    )


# =========================================================
# FIND FASHION IMAGE
# =========================================================

def find_fashion_image(category, colour):

    category = str(category).lower().strip()
    colour = str(colour).lower().strip()

    possible_files = [
        f"{colour}_{category}.jpg",
        f"{colour}_{category}.jpeg",
        f"{colour}_{category}.JPG",
        f"{colour}_{category}.JPEG"
    ]

    for filename in possible_files:

        image_path = os.path.join(
            IMAGE_FOLDER,
            filename
        )

        if os.path.isfile(image_path):
            return "/images/" + filename

    return None


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():

    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gender TEXT NOT NULL,
            season TEXT NOT NULL,
            category TEXT NOT NULL,
            colour TEXT NOT NULL,
            style TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            feedback TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    admin = db.execute("""
        SELECT id FROM users
        WHERE username = ?
    """, ("admin01",)).fetchone()

    if admin is None:

        db.execute("""
            INSERT INTO users
            (username,email,password,role)
            VALUES (?,?,?,?)
        """, (
            "admin01",
            "admin@fashion.com",
            "admin1234",
            "admin"
        ))

    else:

        db.execute("""
            UPDATE users
            SET email=?,
                password=?,
                role=?
            WHERE username=?
        """, (
            "admin@fashion.com",
            "admin1234",
            "admin",
            "admin01"
        ))

    db.commit()
    db.close()


# =========================================================
# PAGE ROUTES
# =========================================================

@app.route("/")
def index():
    return redirect("/register")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/home")
def home_page():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("home.html")


@app.route("/trend")
def trend_page():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("trend.html")


@app.route("/recommendation")
def recommendation_page():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("recommendation.html")


@app.route("/feedback")
def feedback_page():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("feedback.html")


@app.route("/admin")
def admin_page():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return redirect("/home")

    return render_template("admin.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request."
        })

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))

    if username == "":
        return jsonify({
            "success": False,
            "message": "Username is required."
        })

    if len(username) < 6:
        return jsonify({
            "success": False,
            "message": "Username is not valid."
        })

    if email == "":
        return jsonify({
            "success": False,
            "message": "Email is required."
        })

    if password == "":
        return jsonify({
            "success": False,
            "message": "Password is required."
        })

    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password is not valid."
        })

    db = get_db()

    existing = db.execute("""
        SELECT id
        FROM users
        WHERE username = ?
        OR email = ?
    """, (
        username,
        email
    )).fetchone()

    if existing:

        db.close()

        return jsonify({
            "success": False,
            "message": "Account already exists."
        })

    db.execute("""
        INSERT INTO users
        (username,email,password,role)
        VALUES (?,?,?,?)
    """, (
        username,
        email,
        password,
        "user"
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Account created successfully."
    })


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request."
        })

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if username == "" or password == "":
        return jsonify({
            "success": False,
            "message": "Please enter username and password."
        })

    db = get_db()

    user = db.execute("""
        SELECT id,username,email,password,role
        FROM users
        WHERE username=?
        AND password=?
    """, (
        username,
        password
    )).fetchone()

    db.close()

    if user is None:
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        })

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "username": user["username"],
        "role": user["role"]
    })


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/api/current-user")
def current_user():

    if "user_id" not in session:

        return jsonify({
            "logged_in": False
        })

    return jsonify({
        "logged_in": True,
        "username": session.get("username"),
        "role": session.get("role")
    })


# =========================================================
# USER CREATE TREND
# =========================================================

@app.route("/api/create-trend", methods=["POST"])
def create_trend():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login."
        })

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request."
        })

    gender = str(data.get("gender", "")).strip()
    season = str(data.get("season", "")).strip()
    category = str(data.get("category", "")).strip()
    colour = str(data.get("colour", "")).strip()
    style = str(data.get("style", "")).strip()

    valid_genders = [
        "Women",
        "Men",
        "Kids"
    ]

    valid_seasons = [
        "Summer",
        "Winter",
        "Autumn"
    ]

    valid_categories = [
        "Dress",
        "Tops",
        "Jeans",
        "Shirt",
        "Kids"
    ]

    valid_colours = [
        "Lavender",
        "Pink",
        "Black",
        "White",
        "Blue",
        "Purple"
    ]

    valid_styles = [
        "Modern",
        "Western",
        "Casual"
    ]

    if gender not in valid_genders:
        return jsonify({
            "success": False,
            "message": "Invalid gender."
        })

    if season not in valid_seasons:
        return jsonify({
            "success": False,
            "message": "Invalid season."
        })

    if category not in valid_categories:
        return jsonify({
            "success": False,
            "message": "Invalid category."
        })

    if colour not in valid_colours:
        return jsonify({
            "success": False,
            "message": "Invalid colour."
        })

    if style not in valid_styles:
        return jsonify({
            "success": False,
            "message": "Invalid style."
        })

    db = get_db()

    db.execute("""
        INSERT INTO trends
        (
            user_id,
            gender,
            season,
            category,
            colour,
            style
        )
        VALUES (?,?,?,?,?,?)
    """, (
        session["user_id"],
        gender,
        season,
        category,
        colour,
        style
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Trend created successfully."
    })


# =========================================================
# LATEST TREND
# =========================================================

@app.route("/api/latest-trend")
def latest_trend():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login."
        })

    db = get_db()

    trend = db.execute("""
        SELECT
            id,
            gender,
            season,
            category,
            colour,
            style,
            created_at
        FROM trends
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
    """, (
        session["user_id"],
    )).fetchone()

    db.close()

    if trend is None:

        return jsonify({
            "success": False,
            "message": "No trend found."
        })

    return jsonify({
        "success": True,
        "trend": dict(trend)
    })


# =========================================================
# RECOMMENDATION IMAGE
# =========================================================

@app.route("/api/recommendation-image")
def recommendation_image():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login."
        })

    db = get_db()

    trend = db.execute("""
        SELECT category,colour
        FROM trends
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
    """, (
        session["user_id"],
    )).fetchone()

    db.close()

    if trend is None:

        return jsonify({
            "success": False,
            "message": "No trend found."
        })

    image = find_fashion_image(
        trend["category"],
        trend["colour"]
    )

    if image is None:

        return jsonify({
            "success": False,
            "message": "Fashion image not found."
        })

    return jsonify({
        "success": True,
        "image": image
    })


# =========================================================
# SERVE IMAGES
# =========================================================

@app.route("/images/<path:filename>")
def serve_image(filename):

    return send_from_directory(
        IMAGE_FOLDER,
        filename
    )


# =========================================================
# USER FEEDBACK
# =========================================================

@app.route("/api/feedback", methods=["POST"])
def save_feedback():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login."
        })

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request."
        })

    rating = data.get("rating")

    feedback_text = str(
        data.get("feedback", "")
    ).strip()

    try:
        rating = int(rating)

    except:

        return jsonify({
            "success": False,
            "message": "Invalid rating."
        })

    if rating < 1 or rating > 5:

        return jsonify({
            "success": False,
            "message": "Rating must be between 1 and 5."
        })

    if feedback_text == "":

        return jsonify({
            "success": False,
            "message": "Please enter feedback."
        })

    db = get_db()

    db.execute("""
        INSERT INTO feedback
        (
            user_id,
            rating,
            feedback
        )
        VALUES (?,?,?)
    """, (
        session["user_id"],
        rating,
        feedback_text
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Feedback submitted successfully."
    })


# =========================================================
# ADMIN STATS
# =========================================================

@app.route("/api/admin/stats")
def admin_stats():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    db = get_db()

    users = db.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE role='user'
    """).fetchone()["count"]

    trends = db.execute("""
        SELECT COUNT(*) AS count
        FROM trends
    """).fetchone()["count"]

    feedback = db.execute("""
        SELECT COUNT(*) AS count
        FROM feedback
    """).fetchone()["count"]

    db.close()

    return jsonify({
        "success": True,
        "users": users,
        "trends": trends,
        "feedback": feedback
    })


# =========================================================
# ADMIN USERS - GET
# =========================================================

@app.route("/api/admin/users", methods=["GET"])
def admin_get_users():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    db = get_db()

    rows = db.execute("""
        SELECT
            id,
            username,
            email,
            role,
            created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "users": [dict(row) for row in rows]
    })


# =========================================================
# ADMIN USERS - INSERT
# =========================================================

@app.route("/api/admin/users", methods=["POST"])
def admin_insert_user():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    data = request.get_json(silent=True)

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))
    role = str(data.get("role", "user"))

    if not username or not email or not password:

        return jsonify({
            "success": False,
            "message": "All fields are required."
        })

    if role not in ["user", "admin"]:

        return jsonify({
            "success": False,
            "message": "Invalid role."
        })

    db = get_db()

    try:

        db.execute("""
            INSERT INTO users
            (username,email,password,role)
            VALUES (?,?,?,?)
        """, (
            username,
            email,
            password,
            role
        ))

        db.commit()

    except sqlite3.IntegrityError:

        db.close()

        return jsonify({
            "success": False,
            "message": "Username or email already exists."
        })

    db.close()

    return jsonify({
        "success": True,
        "message": "User inserted successfully."
    })


# =========================================================
# ADMIN USERS - UPDATE
# =========================================================

@app.route("/api/admin/users/<int:user_id>", methods=["PUT"])
def admin_update_user(user_id):

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    data = request.get_json(silent=True)

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))
    role = str(data.get("role", "user"))

    if not username or not email:

        return jsonify({
            "success": False,
            "message": "Username and email are required."
        })

    if role not in ["user", "admin"]:

        return jsonify({
            "success": False,
            "message": "Invalid role."
        })

    db = get_db()

    if password:

        db.execute("""
            UPDATE users
            SET username=?,
                email=?,
                password=?,
                role=?
            WHERE id=?
        """, (
            username,
            email,
            password,
            role,
            user_id
        ))

    else:

        db.execute("""
            UPDATE users
            SET username=?,
                email=?,
                role=?
            WHERE id=?
        """, (
            username,
            email,
            role,
            user_id
        ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "User updated successfully."
    })


# =========================================================
# ADMIN USERS - DELETE
# =========================================================

@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    if user_id == session.get("user_id"):

        return jsonify({
            "success": False,
            "message": "Admin cannot delete current account."
        })

    db = get_db()

    db.execute("""
        DELETE FROM trends
        WHERE user_id=?
    """, (user_id,))

    db.execute("""
        DELETE FROM feedback
        WHERE user_id=?
    """, (user_id,))

    db.execute("""
        DELETE FROM users
        WHERE id=?
    """, (user_id,))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "User deleted successfully."
    })


# =========================================================
# ADMIN TRENDS - GET
# =========================================================

@app.route("/api/admin/trends", methods=["GET"])
def admin_get_trends():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    db = get_db()

    rows = db.execute("""
        SELECT
            trends.id,
            trends.user_id,
            users.username,
            trends.gender,
            trends.season,
            trends.category,
            trends.colour,
            trends.style,
            trends.created_at
        FROM trends
        LEFT JOIN users
        ON trends.user_id=users.id
        ORDER BY trends.id DESC
    """).fetchall()

    result = []

    for row in rows:

        item = dict(row)

        item["image"] = find_fashion_image(
            row["category"],
            row["colour"]
        )

        result.append(item)

    db.close()

    return jsonify({
        "success": True,
        "trends": result
    })


# =========================================================
# ADMIN USER LATEST TREND IMAGE
# =========================================================

@app.route("/api/admin/user-latest-trend/<int:user_id>")
def admin_user_latest_trend(user_id):

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    db = get_db()

    trend = db.execute("""
        SELECT
            id,
            gender,
            season,
            category,
            colour,
            style,
            created_at
        FROM trends
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    db.close()

    if trend is None:

        return jsonify({
            "success": False,
            "message": "This user has no trend yet."
        })

    image = find_fashion_image(
        trend["category"],
        trend["colour"]
    )

    return jsonify({
        "success": True,
        "trend": dict(trend),
        "image": image
    })


# =========================================================
# ADMIN TRENDS - INSERT
# =========================================================

@app.route("/api/admin/trends", methods=["POST"])
def admin_insert_trend():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    data = request.get_json(silent=True)

    try:
        user_id = int(data.get("user_id"))
    except:
        return jsonify({
            "success": False,
            "message": "Invalid user."
        })

    gender = str(data.get("gender", "")).strip()
    season = str(data.get("season", "")).strip()
    category = str(data.get("category", "")).strip()
    colour = str(data.get("colour", "")).strip()
    style = str(data.get("style", "")).strip()

    db = get_db()

    user = db.execute("""
        SELECT id FROM users
        WHERE id=?
    """, (user_id,)).fetchone()

    if user is None:

        db.close()

        return jsonify({
            "success": False,
            "message": "User not found."
        })

    db.execute("""
        INSERT INTO trends
        (
            user_id,
            gender,
            season,
            category,
            colour,
            style
        )
        VALUES (?,?,?,?,?,?)
    """, (
        user_id,
        gender,
        season,
        category,
        colour,
        style
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Trend inserted successfully."
    })


# =========================================================
# ADMIN TRENDS - UPDATE
# =========================================================

@app.route("/api/admin/trends/<int:trend_id>", methods=["PUT"])
def admin_update_trend(trend_id):

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    data = request.get_json(silent=True)

    user_id = int(data.get("user_id"))
    gender = str(data.get("gender", "")).strip()
    season = str(data.get("season", "")).strip()
    category = str(data.get("category", "")).strip()
    colour = str(data.get("colour", "")).strip()
    style = str(data.get("style", "")).strip()

    db = get_db()

    db.execute("""
        UPDATE trends
        SET user_id=?,
            gender=?,
            season=?,
            category=?,
            colour=?,
            style=?
        WHERE id=?
    """, (
        user_id,
        gender,
        season,
        category,
        colour,
        style,
        trend_id
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Trend updated successfully."
    })


# =========================================================
# ADMIN TRENDS - DELETE
# =========================================================

@app.route("/api/admin/trends/<int:trend_id>", methods=["DELETE"])
def admin_delete_trend(trend_id):

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    db = get_db()

    db.execute("""
        DELETE FROM trends
        WHERE id=?
    """, (trend_id,))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Trend deleted successfully."
    })


# =========================================================
# ADMIN FEEDBACK - GET
# =========================================================

@app.route("/api/admin/feedback", methods=["GET"])
def admin_get_feedback():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    db = get_db()

    rows = db.execute("""
        SELECT
            feedback.id,
            feedback.user_id,
            users.username,
            feedback.rating,
            feedback.feedback,
            feedback.created_at
        FROM feedback
        LEFT JOIN users
        ON feedback.user_id=users.id
        ORDER BY feedback.id DESC
    """).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "feedback": [dict(row) for row in rows]
    })


# =========================================================
# ADMIN FEEDBACK - INSERT
# =========================================================

@app.route("/api/admin/feedback", methods=["POST"])
def admin_insert_feedback():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    data = request.get_json(silent=True)

    user_id = int(data.get("user_id"))
    rating = int(data.get("rating"))
    feedback_text = str(
        data.get("feedback", "")
    ).strip()

    if rating < 1 or rating > 5:

        return jsonify({
            "success": False,
            "message": "Rating must be between 1 and 5."
        })

    if feedback_text == "":

        return jsonify({
            "success": False,
            "message": "Feedback is required."
        })

    db = get_db()

    db.execute("""
        INSERT INTO feedback
        (
            user_id,
            rating,
            feedback
        )
        VALUES (?,?,?)
    """, (
        user_id,
        rating,
        feedback_text
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Feedback inserted successfully."
    })


# =========================================================
# ADMIN FEEDBACK - UPDATE
# =========================================================

@app.route("/api/admin/feedback/<int:feedback_id>", methods=["PUT"])
def admin_update_feedback(feedback_id):

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    data = request.get_json(silent=True)

    user_id = int(data.get("user_id"))
    rating = int(data.get("rating"))
    feedback_text = str(
        data.get("feedback", "")
    ).strip()

    db = get_db()

    db.execute("""
        UPDATE feedback
        SET user_id=?,
            rating=?,
            feedback=?
        WHERE id=?
    """, (
        user_id,
        rating,
        feedback_text,
        feedback_id
    ))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Feedback updated successfully."
    })


# =========================================================
# ADMIN FEEDBACK - DELETE
# =========================================================

@app.route("/api/admin/feedback/<int:feedback_id>", methods=["DELETE"])
def admin_delete_feedback(feedback_id):

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Access denied."
        }), 403

    db = get_db()

    db.execute("""
        DELETE FROM feedback
        WHERE id=?
    """, (feedback_id,))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Feedback deleted successfully."
    })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    create_database()

    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    print()
    print("==========================================")
    print("     FASHION TREND CREATION SYSTEM")
    print("==========================================")
    print("Database :", DATABASE)
    print("Images   :", IMAGE_FOLDER)
    print("Server   : http://127.0.0.1:5000")
    print("------------------------------------------")
    print("Admin Username : admin01")
    print("Admin Password : admin1234")
    print("==========================================")
    print()

    import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )