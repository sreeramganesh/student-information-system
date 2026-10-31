# Student Information System (SIS)

A comprehensive Student Information System built with a **Flask (Python)** backend, **MySQL** database, and a vanilla **HTML/CSS/JavaScript** frontend.

---

## 🛠️ Prerequisites

Before running the project, ensure you have:
1. **Python 3.10+** (verified working on Python 3.14)
2. **MySQL Server 8.x** running locally (e.g., MySQL Community Server or XAMPP MySQL)
3. A web browser (Chrome, Edge, Firefox, etc.)

---

## 🚀 Quick Start Guide

### 1. Configure the Database

1. Ensure MySQL service is running on your machine.
2. The database configuration is stored in [`backend/.env`](backend/.env):
   ```env
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=sis_db
   DATABASE_URL=mysql+pymysql://root:your_mysql_password@127.0.0.1:3306/sis_db
   JWT_SECRET_KEY=sis_dev_secret_jwt_key_2026_x791a
   FLASK_ENV=development
   CORS_ORIGINS=*
   ```
   *(Adjust `DB_PASSWORD` if your MySQL root password is different)*

3. If setting up a fresh database, import the schema from [`backend/mysql-schema.sql`](backend/mysql-schema.sql):
   ```powershell
   mysql -u root -p sis_db < backend/mysql-schema.sql
   ```

---

### 2. Install Python Dependencies

Open a terminal in the project root directory and run:

```powershell
pip install -r backend/requirements.txt
```

> **Note:** PyMySQL requires the `cryptography` library for MySQL 8+ `caching_sha2_password` authentication (already included in `requirements.txt`).

---

### 3. Test Database Connection

Verify that your backend can communicate with MySQL:

```powershell
python backend/test_connection.py
```

You should see:
```text
Database connection successful!
Connected Database : sis_db
Total Tables Found : 13
ALL DATABASE CHECKS PASSED SUCCESSFULLY!
```

---

### 4. Run the Application

Start the Flask server from the project root:

```powershell
python backend/app.py
```

The application will start at:
👉 **`http://127.0.0.1:5000`** (or `http://localhost:5000`)

---

## 🌐 Navigating the Application

The Flask server automatically serves both the backend API and the frontend pages.

| Page | URL | Description |
| :--- | :--- | :--- |
| **Login / Sign Up** | [`http://localhost:5000/`](http://localhost:5000/) | Main portal entry (defaults to `login.html`) |
| **Student Dashboard** | [`http://localhost:5000/student`](http://localhost:5000/student) | Courses, attendance, marks, fees & transcripts |
| **Faculty Dashboard** | [`http://localhost:5000/faculty`](http://localhost:5000/faculty) | Class management, attendance marking, grading |
| **Admin Dashboard** | [`http://localhost:5000/admin`](http://localhost:5000/admin) | User management, courses, system stats |
| **Alumni Portal** | [`http://localhost:5000/alumni`](http://localhost:5000/alumni) | Alumni network, transcript requests, fee receipts |
| **Profile Completion** | [`http://localhost:5000/complete-profile`](http://localhost:5000/complete-profile) | Admission details form for newly registered students |
| **API Health Check** | [`http://localhost:5000/api/health`](http://localhost:5000/api/health) | Verifies backend status |

---

## 📁 Project Structure

```text
SIS_ORIGINAL/
├── backend/
│   ├── app.py                  # Flask app factory, static file routing, API registration
│   ├── config.py               # Environment configuration & DB connection string builder
│   ├── extensions.py           # SQLAlchemy, Migrate, JWT, Bcrypt initialization
│   ├── models.py               # SQLAlchemy ORM models (Users, Students, Courses, etc.)
│   ├── mysql-schema.sql        # MySQL table definitions and constraints
│   ├── requirements.txt        # Python package dependencies
│   ├── test_connection.py      # Script to verify MySQL connectivity
│   ├── routes/                 # Modular API blueprints
│   │   ├── admin.py
│   │   ├── alumni.py
│   │   ├── auth.py
│   │   ├── faculty.py
│   │   └── students.py
│   └── utils/
│       ├── db.py               # Raw PyMySQL connection helper
│       └── decorators.py       # Role-based access control decorators (@role_required)
└── frontend/
    ├── login.html              # Authentication portal (Student, Faculty, Admin, Alumni)
    ├── student.html            # Student dashboard
    ├── faculty.html            # Faculty portal
    ├── admin.html              # Admin management dashboard
    ├── alumni.html             # Alumni portal
    ├── complete-profile.html   # Post-signup admission profile completion
    ├── api-client.js           # Fetch wrapper for calling backend API with JWT
    ├── dashboard.js            # Shared UI utilities and logout helpers
    └── dashboard.css           # Global stylesheets
```


---

## ☁️ Deployment Guide (GitHub & Vercel)

### 1. Push to GitHub

1. Create a new repository on [GitHub](https://github.com/new) (e.g. `sis-portal`). Do **not** initialize with README or license.
2. Link your local repository and push:
   ```powershell
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
   *(Note: `.env` is automatically ignored by `.gitignore` to protect your credentials).*

---

### 2. Host on Vercel

Because Vercel runs in the cloud, it cannot connect to a local `127.0.0.1` MySQL instance. You will need a cloud-hosted MySQL database (such as **Aiven for MySQL**, **TiDB Cloud**, or **Railway**).

#### Step A: Setup Cloud Database
1. Create a free MySQL database on [Aiven](https://aiven.io/) or [TiDB Cloud](https://tidbcloud.com/).
2. Run [`backend/mysql-schema.sql`](backend/mysql-schema.sql) in your cloud database query console to create the tables.
3. Obtain your cloud database connection string (`DATABASE_URL`).

#### Step B: Deploy to Vercel
1. Log in to [Vercel](https://vercel.com) and click **"Add New..."** → **"Project"**.
2. Select and import your GitHub repository.
3. In **Environment Variables**, add:
   - `DATABASE_URL` = `mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>`
   - `JWT_SECRET_KEY` = `your_strong_random_jwt_secret_key`
   - `FLASK_ENV` = `production`
   - `CORS_ORIGINS` = `*`
   - *(Optional if SSL certificate required)*: `DB_SSL_CA` = `ca.pem`
4. Click **Deploy**. Vercel will build the frontend assets and serverless Python backend automatically!
