# 🎓 Student Information System (SIS)

[![Live Demo](https://img.shields.io/badge/Live_Demo-sis--portal--gold.vercel.app-brightgreen?style=for-the-badge&logo=vercel)](https://sis-portal-gold.vercel.app)

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.14-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![JWT](https://img.shields.io/badge/Auth-JWT%20Bearer-red?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel%20Serverless-black?logo=vercel&logoColor=white)](https://vercel.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-ready, full-stack **Student Information System (SIS)** designed for colleges and universities. Built with a high-performance **Python Flask** REST API, a normalized **MySQL** database, and a responsive **HTML5/CSS3/JavaScript** frontend with role-based access control.

> 🌐 **Live Application URL**: [https://sis-portal-gold.vercel.app](https://sis-portal-gold.vercel.app)

---

## 🌟 Key Capabilities & System Features

### 🔐 1. Authentication & Security
- **JWT (JSON Web Token) Authorization**: Stateless token-based session handling with cryptographic signing. In production, strong random keys are strictly required (insecure fallback defaults are rejected).
- **Bcrypt Password Hashing**: Industry-standard salt rounds ensuring zero plain-text passwords stored.
- **Role-Based Access Control (RBAC)**: Custom Python decorators (`@role_required`) enforce strict role permissions (`student`, `faculty`, `admin`, `alumni`) across all API routes.
- **Restricted Public Registration**: Public self-registration is limited to `student` and `alumni`. Privileged `admin` and `faculty` accounts cannot be self-registered and must be provisioned by administrators via `POST /api/admin/users`.
- **Restricted CORS Policy**: Wildcard (`*`) origin access is blocked in production; strict origin allowlists are enforced for frontend deployments.
- **Frontend Route Guards**: Automated redirect handlers checking token integrity and user roles on page load.

---

### 👥 2. Role-Based Portals

#### 🎓 Student Portal (`/student`)
- **Academic Dashboard**: High-level overview displaying CGPA, overall attendance percentage, enrolled courses, and fee balance.
- **Smart Course Registration & Automatic Waitlist Promotion**: Real-time course catalog with capacity enforcement and concurrency-safe locking (`with_for_update()`). When a course is full, students are placed on an ordered waitlist (`waitlist_position`). When an enrolled student drops a course, the earliest waitlisted student is automatically promoted to confirmed status, and subsequent waitlist positions re-index automatically.
- **Course Drop / Cancellation**: Students can cancel confirmed registrations or leave waitlists at any time from the portal.
- **Subject-Wise Attendance**: Real-time breakdown of classes held vs. attended (`present`, `absent`), percentage tracking, and automatic visual warnings for attendance falling below the mandatory 75% threshold.
- **Grade Cards & Published Results**: Instant view of internal assessments, semester exams, and final letter grades.
- **Fee Management & Receipts**: Complete ledger displaying total tuition fees, amount paid, outstanding balances, and official receipt numbers.
- **Records Office Transcripts**: Request official academic transcripts for internships, higher studies, or employment directly from the portal.

#### 👨‍🏫 Faculty Portal (`/faculty`)
- **Class Rosters**: Instant list of students registered in assigned courses with real-time attendance averages.
- **Attendance Tracker**: Streamlined daily attendance marking (`Present`, `Absent`) with backend constraint validation and automatic deduplication per date.
- **Assessment Marks Entry**: Upload marks for internal assessments, cycle tests, and assignments.
- **Semester Grade Publishing**: Enter internal/external marks and publish final semester grades to students.
- **Faculty Profile Management**: Maintain office hours, department affiliations, and contact details.

#### 🛡️ Administrator Portal (`/admin`)
- **Executive Institutional Metrics**: High-level counters for total student body, active faculty members, course catalog size, total fees outstanding, and overdue accounts.
- **User Directory**: Search and monitor all registered students and faculty records.
- **Course Administration**: Create new academic courses, assign faculty instructors, and configure seat capacities.
- **Financial Auditing**: View all fee transactions, pending payments, and revenue collection.
- **Academic Reports**: Automated analytical reports identifying at-risk students with attendance below 75% and tracking exam result publication progress across departments.

#### 🏛️ Alumni Network Portal (`/alumni`)
- **Career & Profile Records**: Keep graduation year, department, and current employer details updated.
- **Historical Fee Ledgers**: Lifetime access to past payment records and tuition fee clearance statements.
- **Official Transcript Requests**: On-demand transcript applications for graduate school or international verifications with delivery status tracking.

---

### 📝 3. Student Admission & Profile Onboarding (`/complete-profile`)
- **Post-Registration Verification**: Newly registered students complete an institutional admission profile before gaining dashboard access.
- **Personal & Family Data**: Collects DOB, nationality, community category, parent/guardian name, occupation, annual income, and address.
- **Qualifying Examination Records**: Captures board of education, course opted, and subject-wise 12th/HSC marks with automatic aggregate calculation.

---

## 🏗️ Technical Architecture & Stack

```text
SIS/
├── api/
│   └── index.py                # Serverless WSGI entrypoint for Vercel deployment
├── backend/
│   ├── app.py                  # Flask app factory, static/SPA routing, CORS setup
│   ├── config.py               # Environment configuration & DB connection builder
│   ├── extensions.py           # SQLAlchemy, Migrate, JWTManager, Bcrypt setup
│   ├── models.py               # 13 SQLAlchemy ORM models with relations & constraints
│   ├── mysql-schema.sql        # MySQL table definitions, foreign keys, and indexes
│   ├── requirements.txt        # Backend dependencies
│   ├── test_connection.py      # Database connection & schema test script
│   ├── routes/                 # Modular API blueprints
│   │   ├── auth.py             # Signup, login, JWT token verification
│   │   ├── students.py         # Student records, courses, attendance, fees
│   │   ├── faculty.py          # Faculty courses, attendance marking, grading
│   │   ├── admin.py            # System analytics, course catalog, audit reports
│   │   └── alumni.py           # Alumni directory & transcript services
│   └── utils/
│       ├── db.py               # Direct PyMySQL connection helper
│       └── decorators.py       # Role-based access control (@role_required)
├── frontend/
│   ├── login.html              # Multi-role authentication portal (Tabs: Student/Faculty/Admin/Alumni)
│   ├── student.html            # Student dashboard
│   ├── faculty.html            # Faculty portal
│   ├── admin.html              # Administrator overview
│   ├── alumni.html             # Alumni portal
│   ├── complete-profile.html   # Post-signup admission profile onboarding
│   ├── api-client.js           # Fetch wrapper with JWT headers and dynamic origin detection
│   ├── dashboard.js            # Shared UI utilities, mobile navigation, toast messages
│   └── dashboard.css           # Modern design system with CSS custom properties
├── requirements.txt            # Root dependencies for cloud buildpacks (Vercel)
├── vercel.json                 # Vercel serverless rewrites and static asset routing
└── .gitignore                  # Git ignore rules protecting .env and cache files
```

---

## 🗄️ Database Architecture (13 Relational Tables)

The database schema is normalized and optimized with foreign key constraints, cascading deletes, and unique constraints:

| Table | Purpose |
| :--- | :--- |
| `users` | Base authentication table storing credentials, bcrypt hash, role, and email |
| `students` | Student profiles, roll number, department, semester, CGPA, profile completion flag |
| `faculty` | Faculty profiles, faculty code, department, office hours |
| `alumni` | Alumni profiles, graduation batch, employer info |
| `courses` | Academic course catalog, assigned faculty ID, capacity, and seat counters |
| `registrations` | Course registrations with `registered` or `waitlisted` status and queue position |
| `attendance` | Daily attendance records marked by faculty (`present`, `absent`) |
| `marks` | Internal and assessment scores per subject |
| `results` | Final semester examination results (internal, external, grade, published flag) |
| `fees` | Student fee ledger, receipt numbers, amounts, due dates, and payment status |
| `transcript_requests` | Formal transcript requests, purpose, destination email, and processing status |
| `admission_details` | Detailed admission demographic information and parent details |
| `hsc_subject_marks` | Subject-wise qualifying exam marks for admission verification |

---

## 🚀 Local Installation & Quick Start

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.14)
- **MySQL Server 8.0+** (MySQL Community Server or XAMPP)
- **Git**

### 2. Clone and Setup
```powershell
git clone https://github.com/sreeramganesh/student-information-system.git
cd student-information-system
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
Copy the example environment file:
```powershell
cp backend/.env.example backend/.env
```
Update `backend/.env` with your MySQL credentials:
```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=sis_db
DATABASE_URL=mysql+pymysql://root:your_mysql_password@127.0.0.1:3306/sis_db
JWT_SECRET_KEY=your_secret_jwt_key
FLASK_ENV=development
CORS_ORIGINS=*
```

### 5. Initialize the Database
Create the database and tables using the provided SQL schema:
```powershell
mysql -u root -p sis_db < backend/mysql-schema.sql
```

Verify the connection:
```powershell
python backend/test_connection.py
```

### 6. Run the Application
```powershell
python backend/app.py
```
Open your browser and navigate to:
👉 **`http://localhost:5000`**

### 7. Run Automated Test Suite
Execute the comprehensive security, waitlist, attendance, and regression test suite:
```powershell
python backend/test_suite.py
```

---

## ☁️ Deployment on Vercel

This repository includes [`vercel.json`](vercel.json) and [`api/index.py`](api/index.py) configured out of the box for serverless deployment.

1. **Cloud Database**: Create a free cloud MySQL instance on [TiDB Cloud](https://tidbcloud.com/) or [Aiven for MySQL](https://aiven.io/). Import `backend/mysql-schema.sql`.
2. **Import to Vercel**: Go to [vercel.com/new](https://vercel.com/new) and select `student-information-system`.
3. **Environment Variables**: In Vercel Project Settings, add:
   - `DATABASE_URL` = `mysql+pymysql://<user>:<password>@<cloud-host>:<port>/<dbname>`
   - `JWT_SECRET_KEY` = `<your-jwt-secret>`
   - `FLASK_ENV` = `production`
   - `CORS_ORIGINS` = `*`
4. **Deploy**: Click **Deploy**. Vercel will host your static frontend on edge CDN and the Flask API on serverless compute.

👉 **Production Deployment:** [https://sis-portal-gold.vercel.app](https://sis-portal-gold.vercel.app)
