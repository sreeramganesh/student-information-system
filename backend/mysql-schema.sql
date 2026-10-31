-- ============================================================
-- Student Information System — MySQL Schema
-- Run: mysql -u root -p < mysql-schema.sql
-- (Or paste into MySQL Workbench / phpMyAdmin SQL tab)
--
-- NOTE: If you're using Flask-Migrate (flask db upgrade), you do NOT
-- need to run this file — the migration creates these tables for you
-- from models.py. This file is for manual setup, or for your project
-- report/viva where you need to show the raw SQL.
-- ============================================================

CREATE DATABASE IF NOT EXISTS sis_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE sis_db;

-- ============================================================
-- USERS (replaces Supabase auth.users + profiles combined)
-- ============================================================
CREATE TABLE users (
  id            CHAR(36)      PRIMARY KEY,
  full_name     VARCHAR(120)  NOT NULL,
  email         VARCHAR(120)  NOT NULL UNIQUE,
  username      VARCHAR(60)   NOT NULL UNIQUE,
  password_hash VARCHAR(255)  NOT NULL,
  role          VARCHAR(20)   NOT NULL,
  phone         VARCHAR(20),
  created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_users_role CHECK (role IN ('student','faculty','admin','alumni'))
) ENGINE=InnoDB;

-- ============================================================
-- ROLE-SPECIFIC PROFILES
-- ============================================================
CREATE TABLE students (
  id                CHAR(36)      PRIMARY KEY,
  roll_no           VARCHAR(30)   NOT NULL UNIQUE,
  department        VARCHAR(60),
  semester          INT,
  batch_year        INT,
  cgpa              DECIMAL(3,2),
  address           VARCHAR(255),
  profile_completed BOOLEAN       NOT NULL DEFAULT FALSE,
  CONSTRAINT fk_students_user FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE faculty (
  id            CHAR(36)      PRIMARY KEY,
  faculty_code  VARCHAR(30)   NOT NULL UNIQUE,
  department    VARCHAR(60),
  office_hours  VARCHAR(120),
  CONSTRAINT fk_faculty_user FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE alumni (
  id                CHAR(36)      PRIMARY KEY,
  roll_no           VARCHAR(30),
  department        VARCHAR(60),
  batch_year        INT,
  current_employer  VARCHAR(120),
  CONSTRAINT fk_alumni_user FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- ACADEMICS
-- ============================================================
CREATE TABLE courses (
  id            CHAR(36)      PRIMARY KEY,
  name          VARCHAR(120)  NOT NULL,
  department    VARCHAR(60),
  faculty_id    CHAR(36),
  capacity      INT           DEFAULT 60,
  seats_filled  INT           DEFAULT 0,
  created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_courses_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(id)
) ENGINE=InnoDB;

CREATE TABLE registrations (
  id                CHAR(36)      PRIMARY KEY,
  student_id        CHAR(36)      NOT NULL,
  course_id         CHAR(36)      NOT NULL,
  status            VARCHAR(20)   DEFAULT 'registered',
  waitlist_position INT,
  created_at        DATETIME      DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_reg_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_reg_course  FOREIGN KEY (course_id)  REFERENCES courses(id)  ON DELETE CASCADE,
  CONSTRAINT uq_reg_student_course UNIQUE (student_id, course_id),
  CONSTRAINT chk_reg_status CHECK (status IN ('registered','waitlisted'))
) ENGINE=InnoDB;

CREATE TABLE attendance (
  id          CHAR(36)      PRIMARY KEY,
  student_id  CHAR(36)      NOT NULL,
  course_id   CHAR(36)      NOT NULL,
  class_date  DATE          DEFAULT (CURRENT_DATE),
  status      VARCHAR(10)   NOT NULL,
  marked_by   CHAR(36),
  CONSTRAINT fk_att_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_att_course  FOREIGN KEY (course_id)  REFERENCES courses(id)  ON DELETE CASCADE,
  CONSTRAINT fk_att_faculty FOREIGN KEY (marked_by)  REFERENCES faculty(id),
  CONSTRAINT uq_att_student_course_date UNIQUE (student_id, course_id, class_date),
  CONSTRAINT chk_att_status CHECK (status IN ('present','absent'))
) ENGINE=InnoDB;

CREATE TABLE marks (
  id          CHAR(36)      PRIMARY KEY,
  student_id  CHAR(36)      NOT NULL,
  course_id   CHAR(36)      NOT NULL,
  assessment  VARCHAR(60)   NOT NULL,
  marks       DECIMAL(5,2),
  max_marks   DECIMAL(5,2)  DEFAULT 30,
  CONSTRAINT fk_marks_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_marks_course  FOREIGN KEY (course_id)  REFERENCES courses(id)  ON DELETE CASCADE,
  CONSTRAINT uq_marks_student_course_assessment UNIQUE (student_id, course_id, assessment)
) ENGINE=InnoDB;

CREATE TABLE results (
  id          CHAR(36)      PRIMARY KEY,
  student_id  CHAR(36)      NOT NULL,
  course_id   CHAR(36)      NOT NULL,
  internal    DECIMAL(5,2),
  external    DECIMAL(5,2),
  grade       VARCHAR(5),
  published   BOOLEAN       DEFAULT FALSE,
  CONSTRAINT fk_results_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_results_course  FOREIGN KEY (course_id)  REFERENCES courses(id)  ON DELETE CASCADE,
  CONSTRAINT uq_results_student_course UNIQUE (student_id, course_id)
) ENGINE=InnoDB;

CREATE TABLE fees (
  id           CHAR(36)      PRIMARY KEY,
  student_id   CHAR(36)      NOT NULL,   -- references users(id): covers students AND alumni
  receipt_no   VARCHAR(40),
  description  VARCHAR(120),
  amount       DECIMAL(10,2) NOT NULL,
  status       VARCHAR(10)   NOT NULL,
  fee_date     DATE          DEFAULT (CURRENT_DATE),
  CONSTRAINT fk_fees_user FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT chk_fees_status CHECK (status IN ('paid','due','overdue'))
) ENGINE=InnoDB;

CREATE TABLE transcript_requests (
  id              CHAR(36)      PRIMARY KEY,
  student_id      CHAR(36)      NOT NULL,   -- references users(id): covers students AND alumni
  purpose         VARCHAR(120),
  delivery_email  VARCHAR(120),
  status          VARCHAR(20)   DEFAULT 'pending',
  requested_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_transcript_user FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT chk_transcript_status CHECK (status IN ('pending','processing','issued'))
) ENGINE=InnoDB;

-- ============================================================
-- ADMISSION DETAILS (post-signup profile completion)
-- ============================================================
CREATE TABLE admission_details (
  id                    CHAR(36)      PRIMARY KEY,
  student_id            CHAR(36)      NOT NULL UNIQUE,
  date_of_birth         DATE,
  gender                VARCHAR(15),
  nationality           VARCHAR(40)   DEFAULT 'Indian',
  community             VARCHAR(20),
  parent_name           VARCHAR(120),
  parent_occupation     VARCHAR(60),
  parent_annual_income  VARCHAR(20),
  address_line          VARCHAR(255),
  pincode               VARCHAR(10),
  phone                 VARCHAR(20),
  board_of_exam         VARCHAR(30),
  course_opted          VARCHAR(60),
  submitted_at          DATETIME      DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_admission_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT chk_admission_gender CHECK (gender IN ('male','female','transgender')),
  CONSTRAINT chk_admission_community CHECK (community IN ('sc','st','sca','mbc_dnc','bc','bc_muslim','others')),
  CONSTRAINT chk_admission_income CHECK (parent_annual_income IN ('below_50k','50k_1l','1l_2l','2l_3l','above_3l')),
  CONSTRAINT chk_admission_board CHECK (board_of_exam IN ('tn_hsc_academic','tn_hsc_vocational','cbse','isc','others'))
) ENGINE=InnoDB;

CREATE TABLE hsc_subject_marks (
  id              CHAR(36)      PRIMARY KEY,
  student_id      CHAR(36)      NOT NULL,
  subject_name    VARCHAR(60)   NOT NULL,
  max_marks       DECIMAL(5,2)  NOT NULL,
  marks_obtained  DECIMAL(5,2)  NOT NULL,
  CONSTRAINT fk_hsc_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- Helpful indexes for common lookups
-- ============================================================
CREATE INDEX idx_registrations_course ON registrations(course_id);
CREATE INDEX idx_attendance_course ON attendance(course_id);
CREATE INDEX idx_attendance_student ON attendance(student_id);
CREATE INDEX idx_fees_student ON fees(student_id);
