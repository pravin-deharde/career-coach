from flask import render_template, send_file, redirect, url_for, flash, session
from io import BytesIO
from io import BytesIO
from flask import render_template, send_file, redirect, url_for, flash, session
from flask import (
    render_template,
    request,
    redirect,
    flash
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from roadmap_data import roadmaps
from database import db
from database.models import Job
import re
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

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password")
        role = request.form.get("role")

        # Gmail validation
        if not re.fullmatch(r"[a-zA-Z0-9._%+-]+@gmail\.com", email):
            flash("Please enter a valid Gmail address ending with @gmail.com")
            return redirect(url_for("register"))

        # Check if email already exists
        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email already registered")
            return redirect(url_for("register"))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create new user
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
@app.route("/career/details/<path:title>")
def career_details(title):

    print("URL se aaya title:", repr(title))
    print("career_data keys:", list(career_data.keys()))

    for category in career_data.values():

        for course in category:
            if course["title"] == title:
                return render_template(
                    "career_details.html",
                    course=course
                )

    return "Course Not Found"
# -----------------------------
# ROADMAP
# -----------------------------

from roadmap_data import roadmaps

@app.route("/roadmap/<path:course_name>")
def roadmap(course_name):

    if "user_id" not in session:
        return redirect(url_for("login"))

    course_name = course_name.strip()

    print("Requested Course:", repr(course_name))

    roadmap = roadmaps.get(course_name)

    if roadmap is None:
        print("Available Keys:", list(roadmaps.keys()))
        flash(f"Roadmap not found for {course_name}")
        return redirect(url_for("career"))

    return render_template(
        "roadmap_details.html",
        course_name=course_name,
        roadmap=roadmap
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
@app.route("/resume/analyze", methods=["GET","POST"])
def analyze_resume():

    if "user_id" not in session:
        return redirect("/login")

    resume = Resume.query.filter_by(user_id=session["user_id"]).first()

    if not resume:
        flash("Resume not found")
        return redirect("/resume")

    score = 0
    suggestions = []

    if resume.summary and len(resume.summary) > 30:
        score += 10
    else:
        suggestions.append("Add Professional Summary")

    if resume.education:
        score += 10
    else:
        suggestions.append("Add Education")

    if resume.skills:
        score += 15
    else:
        suggestions.append("Add Skills")

    if resume.projects:
        score += 20
    else:
        suggestions.append("Add Projects")

    if resume.experience:
        score += 15
    else:
        suggestions.append("Add Experience")

    if resume.github:
        score += 10
    else:
        suggestions.append("Add GitHub Profile")

    if resume.linkedin:
        score += 10
    else:
        suggestions.append("Add LinkedIn Profile")

    if resume.certifications:
        score += 10
    else:
        suggestions.append("Add Certifications")

    if score >= 90:
        level = "Excellent"
    elif score >= 75:
        level = "Good"
    elif score >= 60:
        level = "Average"
    else:
        level = "Needs Improvement"

    ats_score = score

    missing_skills = []

    required = [
        "Python",
        "SQL",
        "Git",
        "HTML",
        "CSS",
        "JavaScript"
    ]

    resume_skills = ""

    if resume.skills:
        resume_skills = resume.skills.lower()

    for skill in required:

        if skill.lower() not in resume_skills:

            missing_skills.append(skill)

    return render_template(
    "resume_analysis.html",
    score=score,
    ats_score=ats_score,
    level=level,
    suggestions=suggestions,
    missing_skills=missing_skills
)
@app.route("/interview")
def interview():

    questions = [
        {
            "question": "What is Python?",
            "options": [
                "Programming Language",
                "Database",
                "Operating System",
                "Compiler"
            ],
            "answer": "Programming Language"
        },
        {
            "question": "Which keyword is used to define a function in Python?",
            "options": [
                "func",
                "define",
                "def",
                "function"
            ],
            "answer": "def"
        },
        {
            "question": "HTML stands for?",
            "options": [
                "Hyper Text Markup Language",
                "High Text Machine Language",
                "Home Tool Markup Language",
                "Hyper Tool Multi Language"
            ],
            "answer": "Hyper Text Markup Language"
        },
        {
            "question": "CSS is used for?",
            "options": [
                "Styling",
                "Programming",
                "Database",
                "Networking"
            ],
            "answer": "Styling"
        },
        {
            "question": "Which SQL command is used to fetch data?",
            "options": [
                "SELECT",
                "INSERT",
                "DELETE",
                "UPDATE"
            ],
            "answer": "SELECT"
        }
    ]

    return render_template(
        "interview.html",
        questions=questions
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
        flash("Please create your resume first.")
        return redirect(url_for("resume"))

    try:
        from playwright.sync_api import sync_playwright

        # Render the standalone PDF template
        html = render_template(
            "resume_pdf.html",
            resume=resume
        )

        with sync_playwright() as p:

            browser = p.chromium.launch()

            page = browser.new_page(
                viewport={"width": 794, "height": 1123}
            )

            page.set_content(
                html,
                wait_until="load"
            )

            # Wait until the resume content is rendered
            page.locator(".professional-resume").wait_for(
                state="visible"
            )

            # Check that the resume has actual content
            content = page.locator(
                ".professional-resume"
            ).inner_text()

            if not content.strip():
                browser.close()
                flash("Resume content is empty. Please save your details first.")
                return redirect(url_for("resume"))

            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                margin={
                    "top": "10mm",
                    "bottom": "10mm",
                    "left": "10mm",
                    "right": "10mm"
                }
            )

            browser.close()

        return send_file(
            BytesIO(pdf_bytes),
            as_attachment=True,
            download_name="Professional_Resume.pdf",
            mimetype="application/pdf"
        )

    except Exception:
        app.logger.exception("Resume PDF generation failed")
        flash("PDF generation failed. Please check the terminal logs.")
        return redirect(url_for("resume"))
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

    recommendations = []
    student_name = ""

    career_data = {
        "Programming": {
            "careers": [
                {
                    "title": "Software Developer",
                    "skills": ["Python", "Java", "DSA", "SQL"],
                    "reason": "Suitable for students interested in logic, coding and problem-solving.",
                    "roadmap": [
                        "Learn Python or Java fundamentals",
                        "Practice data structures and algorithms",
                        "Learn SQL and Git",
                        "Build 2-3 practical projects"
                    ]
                },
                {
                    "title": "Backend Developer",
                    "skills": ["Python", "Flask", "APIs", "Databases"],
                    "reason": "A possible path for students interested in server-side development.",
                    "roadmap": [
                        "Learn Python fundamentals",
                        "Learn Flask and REST APIs",
                        "Practice database operations",
                        "Build and deploy a web application"
                    ]
                },
                {
                    "title": "Software Tester",
                    "skills": ["Testing", "Python", "SQL", "Automation"],
                    "reason": "Worth exploring if you enjoy finding errors and improving software quality.",
                    "roadmap": [
                        "Learn software testing fundamentals",
                        "Practice writing test cases",
                        "Learn SQL basics",
                        "Explore automated testing tools"
                    ]
                }
            ]
        },

        "Web Development": {
            "careers": [
                {
                    "title": "Frontend Developer",
                    "skills": ["HTML", "CSS", "JavaScript", "React"],
                    "reason": "Suitable for students interested in website interfaces and user experience.",
                    "roadmap": [
                        "Learn HTML and CSS",
                        "Practice JavaScript",
                        "Build responsive websites",
                        "Learn React and create a portfolio"
                    ]
                },
                {
                    "title": "Backend Developer",
                    "skills": ["Python", "Flask", "SQL", "APIs"],
                    "reason": "Suitable for students interested in application logic and databases.",
                    "roadmap": [
                        "Learn Python",
                        "Learn Flask",
                        "Practice SQL",
                        "Build and deploy an application"
                    ]
                },
                {
                    "title": "Full Stack Developer",
                    "skills": ["HTML", "CSS", "JavaScript", "Python", "SQL"],
                    "reason": "Combines frontend and backend development.",
                    "roadmap": [
                        "Learn frontend fundamentals",
                        "Learn a backend framework",
                        "Connect applications to databases",
                        "Build a complete web project"
                    ]
                }
            ]
        },

        "Artificial Intelligence": {
            "careers": [
                {
                    "title": "AI/ML Engineer",
                    "skills": ["Python", "Statistics", "Linear Algebra", "Machine Learning"],
                    "reason": "A potential path for students interested in programming, mathematics and intelligent systems.",
                    "roadmap": [
                        "Learn Python",
                        "Study statistics and linear algebra",
                        "Learn machine learning fundamentals",
                        "Build and evaluate ML projects"
                    ]
                },
                {
                    "title": "Data Scientist",
                    "skills": ["Python", "Statistics", "SQL", "Data Analysis"],
                    "reason": "Combines data analysis, statistics and programming.",
                    "roadmap": [
                        "Learn Python and SQL",
                        "Study statistics",
                        "Practice data analysis",
                        "Build data science projects"
                    ]
                },
                {
                    "title": "AI Application Developer",
                    "skills": ["Python", "APIs", "Prompt Design", "Software Development"],
                    "reason": "Suitable for students interested in building applications using AI services.",
                    "roadmap": [
                        "Learn programming fundamentals",
                        "Understand APIs",
                        "Learn responsible AI integration",
                        "Build an AI-powered application"
                    ]
                }
            ]
        },

        "Data Science": {
            "careers": [
                {
                    "title": "Data Analyst",
                    "skills": ["Excel", "SQL", "Python", "Power BI"],
                    "reason": "Suitable for students interested in finding insights from data.",
                    "roadmap": [
                        "Learn Excel",
                        "Learn SQL",
                        "Practice Python and pandas",
                        "Create dashboards and portfolio projects"
                    ]
                },
                {
                    "title": "Business Intelligence Analyst",
                    "skills": ["SQL", "Excel", "Power BI", "Statistics"],
                    "reason": "Combines business questions with data reporting.",
                    "roadmap": [
                        "Learn spreadsheets",
                        "Practice SQL",
                        "Learn Power BI",
                        "Build interactive dashboards"
                    ]
                },
                {
                    "title": "Junior Data Scientist",
                    "skills": ["Python", "Statistics", "SQL", "Machine Learning"],
                    "reason": "A longer-term option for students who enjoy statistics and analytical problem-solving.",
                    "roadmap": [
                        "Learn Python and SQL",
                        "Study statistics",
                        "Practice data cleaning and visualization",
                        "Explore machine learning projects"
                    ]
                }
            ]
        },

        "Cyber Security": {
            "careers": [
                {
                    "title": "Security Analyst",
                    "skills": ["Networking", "Linux", "Security Fundamentals", "SIEM"],
                    "reason": "Suitable for students interested in protecting systems and investigating security alerts.",
                    "roadmap": [
                        "Learn computer networking",
                        "Practice Linux fundamentals",
                        "Study security principles",
                        "Use legal cybersecurity labs"
                    ]
                },
                {
                    "title": "Security Engineer",
                    "skills": ["Networking", "Linux", "Scripting", "Cloud Security"],
                    "reason": "A potential path for students interested in designing and maintaining secure systems.",
                    "roadmap": [
                        "Learn networking and operating systems",
                        "Practice scripting",
                        "Study security architecture",
                        "Build defensive security projects"
                    ]
                },
                {
                    "title": "Application Security Tester",
                    "skills": ["Web Development", "Networking", "OWASP", "Testing"],
                    "reason": "Suitable for students interested in finding and preventing application vulnerabilities.",
                    "roadmap": [
                        "Learn web fundamentals",
                        "Study common web vulnerabilities",
                        "Practice in authorized training labs",
                        "Learn secure coding and reporting"
                    ]
                }
            ]
        },

        "Business": {
            "careers": [
                {
                    "title": "Business Analyst",
                    "skills": ["Excel", "SQL", "Communication", "Requirements Analysis"],
                    "reason": "Suitable for students interested in solving business problems using information and analysis.",
                    "roadmap": [
                        "Learn Excel",
                        "Develop communication skills",
                        "Study business processes",
                        "Practice documenting requirements"
                    ]
                },
                {
                    "title": "Digital Marketing Specialist",
                    "skills": ["SEO", "Content Strategy", "Analytics", "Communication"],
                    "reason": "Suitable for students interested in marketing, content and audience behaviour.",
                    "roadmap": [
                        "Learn digital marketing fundamentals",
                        "Study SEO and content strategy",
                        "Practice analytics",
                        "Create a sample campaign"
                    ]
                },
                {
                    "title": "Entrepreneur",
                    "skills": ["Market Research", "Finance", "Communication", "Planning"],
                    "reason": "An option for students interested in building and managing a business.",
                    "roadmap": [
                        "Identify a customer problem",
                        "Research the market",
                        "Prepare a simple business plan",
                        "Test the idea on a small scale"
                    ]
                }
            ]
        },

        "Design": {
            "careers": [
                {
                    "title": "UI/UX Designer",
                    "skills": ["Figma", "Wireframing", "Prototyping", "User Research"],
                    "reason": "Suitable for students interested in user-friendly digital products.",
                    "roadmap": [
                        "Learn design fundamentals",
                        "Practice Figma",
                        "Create wireframes and prototypes",
                        "Build a design portfolio"
                    ]
                },
                {
                    "title": "Graphic Designer",
                    "skills": ["Typography", "Layout", "Colour Theory", "Design Tools"],
                    "reason": "Suitable for students interested in visual communication.",
                    "roadmap": [
                        "Study visual design fundamentals",
                        "Practice design software",
                        "Create posters and brand concepts",
                        "Build a portfolio"
                    ]
                },
                {
                    "title": "Web Designer",
                    "skills": ["UI Design", "Figma", "HTML", "CSS"],
                    "reason": "Combines visual design with website layout and usability.",
                    "roadmap": [
                        "Learn layout and typography",
                        "Practice Figma",
                        "Understand HTML and CSS",
                        "Design and publish sample websites"
                    ]
                }
            ]
        },

        "Medical": {
            "careers": [
                {
                    "title": "Doctor (MBBS)",
                    "skills": ["Biology", "Chemistry", "Physics", "Clinical Learning"],
                    "reason": "For eligible students interested in patient care. In India, MBBS admission generally requires the applicable NEET-UG and eligibility requirements.",
                    "roadmap": [
                        "Check current eligibility requirements",
                        "Prepare Physics, Chemistry and Biology",
                        "Qualify through the applicable admission process",
                        "Complete the recognised medical degree and required training"
                    ]
                },
                {
                    "title": "Pharmacist",
                    "skills": ["Pharmaceutical Science", "Chemistry", "Biology", "Accuracy"],
                    "reason": "A healthcare-related option requiring the appropriate recognised pharmacy qualification and registration where applicable.",
                    "roadmap": [
                        "Research recognised pharmacy courses",
                        "Check admission eligibility",
                        "Complete the required qualification",
                        "Meet applicable registration requirements"
                    ]
                },
                {
                    "title": "Allied Healthcare Professional",
                    "skills": ["Biology", "Patient Care", "Clinical Procedures", "Communication"],
                    "reason": "Explore recognised allied-health programmes based on your interests and eligibility.",
                    "roadmap": [
                        "Explore recognised allied-health courses",
                        "Check eligibility and accreditation",
                        "Complete the required training",
                        "Gain supervised clinical experience"
                    ]
                }
            ]
        },

        "Government Jobs": {
            "careers": [
                {
                    "title": "State Government Services",
                    "skills": ["General Knowledge", "Reasoning", "Language", "Current Affairs"],
                    "reason": "Potential option for candidates who meet the eligibility requirements of relevant state recruitment exams.",
                    "roadmap": [
                        "Choose a specific state exam",
                        "Read its latest official notification",
                        "Study the prescribed syllabus",
                        "Practice mock tests and previous papers"
                    ]
                },
                {
                    "title": "Civil Services",
                    "skills": ["General Studies", "Current Affairs", "Writing", "Analysis"],
                    "reason": "A competitive pathway with specific eligibility conditions and a demanding examination process.",
                    "roadmap": [
                        "Check the official examination eligibility",
                        "Study the prescribed syllabus",
                        "Develop reading and answer-writing skills",
                        "Practice previous papers and mock tests"
                    ]
                },
                {
                    "title": "Banking Exams",
                    "skills": ["Quantitative Aptitude", "Reasoning", "English", "Banking Awareness"],
                    "reason": "An option for candidates who meet the relevant recruitment notification's requirements.",
                    "roadmap": [
                        "Select an appropriate banking exam",
                        "Check its official eligibility",
                        "Prepare aptitude and reasoning",
                        "Practice timed mock tests"
                    ]
                }
            ]
        }
    }

    if request.method == "POST":

        student_name = request.form.get("name", "").strip()
        qualification = request.form.get("qualification", "").strip()
        subject = request.form.get("subject", "").strip()
        interest = request.form.get("interest", "").strip()

        if not student_name or not interest:
            flash("Please enter your name and select an interest.")
        else:
            selected = career_data.get(interest, {}).get("careers", [])

            # Qualification-aware filtering:
            # Medical degrees and government exams have separate eligibility rules.
            if qualification in ["10th", "12th Science", "12th Commerce", "12th Arts"]:
                recommendations = selected[:3]
            else:
                recommendations = selected[:3]

            # Add the student's subject as context, not as a false eligibility check.
            if subject:
                for item in recommendations:
                    item["reason"] += (
                        f" Your favourite subject is {subject}; consider how it connects "
                        "to this field before choosing."
                    )

    return render_template(
        "ai_career.html",
        recommendations=recommendations,
        student_name=student_name
    )
from flask import request, render_template
import os

@app.route("/recommended_jobs")
def recommended_jobs():

    jobs = [

        {
            "title": "Python Developer",
            "company": "TCS",
            "location": "Pune",
            "salary": "₹5-8 LPA",
            "skills": "Python, Flask, SQL"
        },

        {
            "title": "Full Stack Developer",
            "company": "Infosys",
            "location": "Bangalore",
            "salary": "₹6-10 LPA",
            "skills": "HTML, CSS, JavaScript, Flask"
        },

        {
            "title": "Data Analyst",
            "company": "Accenture",
            "location": "Mumbai",
            "salary": "₹5-9 LPA",
            "skills": "Python, SQL, Excel"
        },

        {
            "title": "AI Engineer",
            "company": "Google",
            "location": "Hyderabad",
            "salary": "₹15-30 LPA",
            "skills": "Python, Machine Learning"
        }

    ]

    return render_template(
        "recommended_jobs.html",
        jobs=jobs
    )
@app.route("/analytics")
def analytics():

    data = {
        "resume_score": 85,
        "interview_score": 78,
        "jobs_applied": 6,
        "roadmaps_completed": 3,
        "courses_explored": 12
    }

    return render_template(
        "analytics.html",
        data=data
    )
@app.route("/admin")
def admin():

    jobs = Job.query.all()

    return render_template(
        "admin.html",
        jobs=jobs
    )
@app.route("/admin/add_job", methods=["GET", "POST"])
def add_job():

    if request.method == "POST":

        job = Job(
            title=request.form["title"],
            company=request.form["company"],
            location=request.form["location"],
            salary=request.form["salary"],
            description=request.form["description"]
        )

        db.session.add(job)
        db.session.commit()

        flash("Job Added Successfully!", "success")

        return redirect("/admin")

    return render_template("add_job.html")
# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)
