from data.career_data import career_data
from data.roadmap_data import roadmaps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import User, Job, Resume, JobApplication
from config import Config
from database import db
import os
from werkzeug.utils import secure_filename
from io import BytesIO
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import func
app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

UPLOAD_FOLDER = os.path.join("static", "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# -----------------------------
# HOME
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# REGISTER
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name")

        email = request.form.get("email")

        password = request.form.get("password")

        role = request.form.get("role")


        user = User.query.filter_by(email=email).first()

        if user:

            flash("Email already registered")

            return redirect(url_for("register"))


        hashed_password = generate_password_hash(password)


        new_user = User(

            full_name=full_name,

            email=email,

            password=hashed_password,

            role=role

        )

        db.session.add(new_user)

        db.session.commit()

        flash("Registration Successful")

        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# LOGIN
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")

        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id

            session["user_name"] = user.full_name

            session["role"] = user.role

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password")

    return render_template("login.html")


# -----------------------------
# DASHBOARD
# -----------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    total_jobs = Job.query.count()

    total_resumes = Resume.query.count()

    applied_jobs = JobApplication.query.filter_by(
        user_id=session["user_id"]
    ).count()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        role=session["role"],
        total_jobs=total_jobs,
        total_resumes=total_resumes,
        applied_jobs=applied_jobs
    )
# -----------------------------
# PROFILE
# -----------------------------

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    return render_template(
        "profile.html",
        user=user
    )


# -----------------------------
# CAREER PAGE
# -----------------------------

@app.route("/career")
def career():

    return render_template("career_home.html")
@app.route("/career/<category>")
def career_category(category):

    courses = career_data.get(category, [])

    return render_template(

        "career_list.html",

        courses=courses,

        category=category

    )
@app.route("/career/details/<title>")
def career_details(title):

    print("Title =", repr(title))

    for category in career_data.values():
        for course in category:
            print(course["title"])
            if course["title"] == title:
                return render_template(
                    "career_details.html",
                    course=course
                )

    return "Course Not Found"

# -----------------------------
# ROADMAP
# -----------------------------

@app.route("/roadmap/<course_name>")
def roadmap(course_name):

    if "user_id" not in session:
        return redirect(url_for("login"))
    print("Course Name:", repr(course_name))
    roadmap = roadmaps.get(course_name)

    if roadmap is None:
        flash("Roadmap not available.")
        return redirect(url_for("career"))

    return render_template(
        "roadmap_details.html",
        roadmap=roadmap,
        course_name=course_name
    )
# -----------------------------
# JOBS
# -----------------------------

@app.route("/jobs")
def jobs():

    if "user_id" not in session:
        return redirect(url_for("login"))

    keyword = request.args.get("search", "")

    if keyword:

        jobs = Job.query.filter(
            Job.title.ilike(f"%{keyword}%")
        ).all()

    else:

        jobs = Job.query.all()

    return render_template(
        "jobs.html",
        jobs=jobs,
        keyword=keyword
    )

# -----------------------------
# RESUME
# -----------------------------

@app.route("/resume", methods=["GET", "POST"])
def resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    resume = Resume.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if request.method == "POST":

        if not resume:
            resume = Resume(user_id=session["user_id"])
            db.session.add(resume)

        resume.name = request.form.get("name")
        resume.email = request.form.get("email")
        resume.phone = request.form.get("phone")
        resume.summary = request.form.get("summary")
        resume.education = request.form.get("education")
        resume.skills = request.form.get("skills")
        resume.projects = request.form.get("projects")
        resume.experience = request.form.get("experience")
        resume.certifications = request.form.get("certifications")
        resume.languages = request.form.get("languages")
        resume.github = request.form.get("github")
        resume.linkedin = request.form.get("linkedin")
        resume.template = request.form.get("template")

        photo = request.files.get("photo")

        if photo and photo.filename != "":

            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            resume.photo = filename

        db.session.commit()

        flash("Professional Resume Saved Successfully!")

        return redirect(url_for("resume"))

    return render_template(
        "resume.html",
        resume=resume
    )
@app.route("/apply/<int:job_id>")
def apply_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    already = JobApplication.query.filter_by(
        job_id=job_id,
        user_id=session["user_id"]
    ).first()

    if already:
        flash("You have already applied for this job.")
        return redirect(url_for("jobs"))

    application = JobApplication(
        job_id=job_id,
        user_id=session["user_id"]
    )

    db.session.add(application)
    db.session.commit()

    flash("Job Applied Successfully!")

    return redirect(url_for("jobs"))
@app.route("/company/applicants/<int:job_id>")
def view_applicants(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        flash("Access Denied")
        return redirect(url_for("dashboard"))

    applications = (
        db.session.query(JobApplication, User)
        .join(User, JobApplication.user_id == User.id)
        .filter(JobApplication.job_id == job_id)
        .all()
    )

    return render_template(
        "applicants.html",
        applications=applications
    )
@app.route("/resume/download")
def download_resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    resume = Resume.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not resume:
        flash("Resume not found.")
        return redirect(url_for("resume"))

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph("<b><font size=20>Professional Resume</font></b>", styles["Title"])
    )

    story.append(
        Paragraph(f"<b>Name:</b> {resume.name}", styles["Heading2"])
    )

    story.append(
        Paragraph(f"<b>Email:</b> {resume.email}", styles["Normal"])
    )

    story.append(
        Paragraph(f"<b>Phone:</b> {resume.phone}", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>Professional Summary</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.summary or "-", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>Education</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.education or "-", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>Skills</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.skills or "-", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>Projects</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.projects or "-", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>Experience</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.experience or "-", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>Certifications</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.certifications or "-", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>Languages</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.languages or "-", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>GitHub</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.github or "-", styles["Normal"])
    )

    story.append(
        Paragraph("<br/><b>LinkedIn</b>", styles["Heading2"])
    )

    story.append(
        Paragraph(resume.linkedin or "-", styles["Normal"])
    )

    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Professional_Resume.pdf",
        mimetype="application/pdf"
    )

@app.route("/resume/scan")
def resume_scan():

    if "user_id" not in session:
        return redirect(url_for("login"))

    resume = Resume.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not resume:
        flash("Please create your resume first.")
        return redirect(url_for("resume"))

    score = 40
    suggestions = []

    if resume.summary:
        score += 10
    else:
        suggestions.append("Add Professional Summary")

    if resume.skills:
        score += 10
    else:
        suggestions.append("Add Skills")

    if resume.projects:
        score += 10
    else:
        suggestions.append("Add Projects")

    if resume.experience:
        score += 10
    else:
        suggestions.append("Add Experience")

    if resume.github:
        score += 5
    else:
        suggestions.append("Add GitHub Profile")

    if resume.linkedin:
        score += 5
    else:
        suggestions.append("Add LinkedIn Profile")

    if resume.certifications:
        score += 5
    else:
        suggestions.append("Add Certifications")

    if resume.languages:
        score += 5
    else:
        suggestions.append("Add Languages")

    return render_template(
        "resume_scan.html",
        score=score,
        suggestions=suggestions
    )
@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":

        user.full_name = request.form.get("full_name")

        user.email = request.form.get("email")

        photo = request.files.get("photo")

        if photo and photo.filename != "":

            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            user.profile_photo = filename

        db.session.commit()

        session["user_name"] = user.full_name

        flash("Profile Updated Successfully!")

        return redirect(url_for("profile"))

    return render_template(
        "edit_profile.html",
        user=user
    )
@app.route("/application/accept/<int:id>")
def accept_application(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    application = JobApplication.query.get_or_404(id)

    application.status = "Accepted"

    db.session.commit()

    flash("Applicant Accepted Successfully!")

    return redirect(
        url_for(
            "view_applicants",
            job_id=application.job_id
        )
    )


@app.route("/application/reject/<int:id>")
def reject_application(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    application = JobApplication.query.get_or_404(id)

    application.status = "Rejected"

    db.session.commit()

    flash("Applicant Rejected Successfully!")

    return redirect(
        url_for(
            "view_applicants",
            job_id=application.job_id
        )
    )
@app.route("/admin/delete-user/<int:id>")
def delete_user(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        flash("Access Denied")
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(id)

    if user.role == "admin":
        flash("Admin account cannot be deleted.")
        return redirect(url_for("admin_dashboard"))

    db.session.delete(user)
    db.session.commit()

    flash("User Deleted Successfully!")

    return redirect(url_for("admin_dashboard"))
@app.route("/company/delete-job/<int:id>")
def delete_job(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        flash("Access Denied")
        return redirect(url_for("dashboard"))

    job = Job.query.get_or_404(id)

    db.session.delete(job)
    db.session.commit()

    flash("Job Deleted Successfully!")

    return redirect(url_for("company_dashboard"))
# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully")

    return redirect(url_for("login"))
# -----------------------------
# COMPANY DASHBOARD
# -----------------------------

@app.route("/company/dashboard")
def company_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        flash("Access Denied")
        return redirect(url_for("dashboard"))

    jobs = Job.query.filter_by(posted_by=session["user_id"]).all()

    return render_template(
        "company_dashboard.html",
        jobs=jobs
    )


# -----------------------------
# POST JOB
# -----------------------------

@app.route("/company/post-job", methods=["GET", "POST"])
def post_job():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "company":
        flash("Access Denied")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        title = request.form.get("title")
        company = request.form.get("company")
        location = request.form.get("location")
        salary = request.form.get("salary")
        description = request.form.get("description")

        job = Job(
            title=title,
            company=company,
            location=location,
            salary=salary,
            description=description,
            posted_by=session["user_id"]
        )

        db.session.add(job)
        db.session.commit()

        flash("Job Posted Successfully")

        return redirect(url_for("company_dashboard"))

    return render_template("post_job.html")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------

@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        flash("Access Denied")
        return redirect(url_for("dashboard"))

    total_users = User.query.count()
    total_jobs = Job.query.count()
    total_resumes = Resume.query.count()

    users = User.query.all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_jobs=total_jobs,
        total_resumes=total_resumes,
        users=users
    )


# -----------------------------
# ERROR HANDLERS
# -----------------------------

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500

@app.route("/ai-career", methods=["GET", "POST"])
def ai_career():

    career = None
    reason = None

    if request.method == "POST":

        interest = request.form.get("interest")

        if interest == "Programming":
            career = "Software Engineer"
            reason = "Programming me interest hai. Python, Java aur Web Development seekho."

        elif interest == "Business":
            career = "Business Analyst"
            reason = "Management aur Business tumhare liye best rahega."

        elif interest == "Medical":
            career = "Doctor"
            reason = "Medical field me achha scope hai."

        elif interest == "Design":
            career = "UI/UX Designer"
            reason = "Creative field tumhare liye best hai."

        elif interest == "Government Jobs":
            career = "UPSC / MPSC Officer"
            reason = "Government Exams ki preparation start karo."

        else:
            career = "Career Counsellor Required"
            reason = "Please explore multiple career options."

    return render_template(
        "ai_career.html",
        career=career,
        reason=reason
    )
@app.route("/ai-resume", methods=["GET","POST"])
def ai_resume():

    score = None

    missing = []

    suggestions = []

    keywords = [

        "python",

        "sql",

        "git",

        "github",

        "flask",

        "html",

        "css",

        "javascript",

        "aws",

        "docker"

    ]

    if request.method == "POST":

        resume = request.form["resume"].lower()

        found = 0

        for skill in keywords:

            if skill in resume:

                found += 1

            else:

                missing.append(skill.upper())

        score = int(found / len(keywords) * 100)

        if score < 40:

            suggestions.append("Resume needs major improvements.")

        elif score < 70:

            suggestions.append("Add more technical skills.")

        else:

            suggestions.append("Excellent ATS Resume.")

        suggestions.append("Add GitHub Profile")

        suggestions.append("Add LinkedIn Profile")

        suggestions.append("Add 2 Projects")

        suggestions.append("Use Action Verbs")

    return render_template(

        "ai_resume.html",

        score=score,

        missing=missing,

        suggestions=suggestions

    )
# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)
