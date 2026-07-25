from database import db

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    profile_photo = db.Column(db.String(255))

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="student")

    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Job(db.Model):

    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)

    company = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(100))

    salary = db.Column(db.String(50))

    description = db.Column(db.Text)

    posted_by = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Resume(db.Model):

    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    education = db.Column(db.Text)

    skills = db.Column(db.Text)

    projects = db.Column(db.Text)

    experience = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

class JobApplication(db.Model):

    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Applied"
    )

    applied_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )