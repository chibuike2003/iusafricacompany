from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import uuid
import re
from sqlalchemy import func, cast, Date # Import func, cast, and Date for date operations

app = Flask(__name__) # Corrected: __init__ to __name__

# --- Configuration ---
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iusafricasoftware.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'teamchampstechnologieslimited@gmail.com'
app.config['MAIL_PASSWORD'] = 'YOUR_GENERATED_APP_PASSWORD_HERE' # Replace with your App Password
app.config['MAIL_DEFAULT_SENDER'] = 'teamchampstechnologieslimited@gmail.com'
mail = Mail(app)

UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    job_title = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    industry = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    onboarded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Business {self.business_name}>'

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user_email = db.Column(db.String(120), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityLog {self.action} by {self.user_email} at {self.timestamp}>'

class RegularUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    profile_picture_filename = db.Column(db.String(255), nullable=True)
    state_of_origin = db.Column(db.String(100), nullable=False)
    lga = db.Column(db.String(100), nullable=False)
    residential_address = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    bio = db.Column(db.Text, nullable=True) # Added bio field
    interests = db.Column(db.String(255), nullable=True) # Added interests field

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<RegularUser {self.email}>'

# New model for Problem Reports
class ProblemReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('regular_user.id'), nullable=True)
    user_name = db.Column(db.String(100), nullable=True)
    user_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Open') # e.g., Open, In Progress, Closed

    def __repr__(self):
        return f'<ProblemReport {self.subject} by {self.user_email}>'

# New model for Contact Messages
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('regular_user.id'), nullable=True)
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='New') # e.g., New, Replied, Archived

    def __repr__(self):
        return f'<ContactMessage {self.subject} from {self.sender_email}>'

# New model for Testimonials
class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('regular_user.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    testimonial_text = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False) # Admin needs to approve before display

    def __repr__(self):
        return f'<Testimonial {self.user_name} - {self.submitted_at}>'

# New model for Blog Posts
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('regular_user.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Pending') # e.g., Pending, Published, Rejected

    def __repr__(self):
        return f'<BlogPost {self.title} by {self.user_name}>'

# New model for Notifications
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('regular_user.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    recipient = db.relationship('RegularUser', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f'<Notification {self.subject} for User {self.user_id}>'



# New model for Comments
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('regular_user.id'), nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True) # For replies
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    # Use primaryjoin to prevent SQLAlchemy from creating a new foreign key constraint
    # on the 'Comment' table for the 'replies' relationship.
    blog_post = db.relationship('BlogPost', backref=db.backref('comments', lazy=True))
    author = db.relationship('RegularUser', backref=db.backref('comments_made', lazy=True))
    parent_comment = db.relationship('Comment', remote_side=[id], backref=db.backref('replies', lazy=True))

    def __repr__(self):
        return f'<Comment {self.id} on Post {self.blog_post_id} by {self.user_id}>'


# NEW MODELS FOR CONTENT MANAGEMENT
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True) # Can be set to false for drafts

    def __repr__(self):
        return f'<Announcement {self.title}>'

class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500), nullable=True) # External link for application/more info
    deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Opportunity {self.title}>'

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    resource_type = db.Column(db.String(50), nullable=False) # 'ebook', 'webinar', 'article', 'toolkit'
    file_link = db.Column(db.String(500), nullable=True) # For ebooks/toolkits (e.g., PDF link)
    video_link = db.Column(db.String(500), nullable=True) # For webinars (e.g., YouTube link)
    content = db.Column(db.Text, nullable=True) # For articles (actual text content)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Resource {self.title} ({self.resource_type})>'



# NEW MODEL FOR EVENTS
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True) # Stores filename of the image
    video_link = db.Column(db.String(500), nullable=True) # External link for video (e.g., YouTube)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Event {self.title} on {self.event_date.strftime("%Y-%m-%d")}>'


# Helper function to log activities
def log_activity(user_id, user_email, action, details=None):
    try:
        log_entry = ActivityLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        db.session.rollback()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---

# Correctly define and assign EVENT_IMAGE_UPLOAD_FOLDER to app.config
EVENT_IMAGE_UPLOAD_FOLDER = 'static/event_images'
ALLOWED_EVENT_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['EVENT_IMAGE_UPLOAD_FOLDER'] = EVENT_IMAGE_UPLOAD_FOLDER


# At the top of your app.py, define the allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_event_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ... rest of your app.py code ...

# Inside your admin_add_event function:
# ...
    image_filename = None
    if image_file and image_file.filename != '':
        if allowed_event_image_file(image_file.filename): # This line will now find the function
            unique_filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['EVENT_IMAGE_UPLOAD_FOLDER'], unique_filename)
            image_file.save(filepath)
            image_filename = unique_filename
        else:
            flash('Invalid image file type. Allowed types are png, jpg, jpeg, gif.', 'error')
            return redirect(url_for('admin_events'))
# ...

@app.route('/')
def index():
    # Fetch latest approved testimonials (e.g., limit to 3 for homepage)
    approved_testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.submitted_at.desc()).limit(3).all()
    # Fetch latest published blog posts (e.g., limit to 3 for homepage)
    recent_blog_posts = BlogPost.query.filter_by(status='Published').order_by(BlogPost.created_at.desc()).limit(3).all()

    return render_template('index.html',
                           approved_testimonials=approved_testimonials,
                           recent_blog_posts=recent_blog_posts)


@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        full_name = request.form.get('full-name')
        email = request.form.get('email')
        phone_number = request.form.get('phone-number')
        job_title = request.form.get('job-title')
        department = request.form.get('department')
        employee_id = request.form.get('employee-id')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if not all([full_name, email, job_title, password, confirm_password]):
            flash('Please fill in all required fields.', 'error')
            return render_template('admin_signup.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('admin_signup.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login or use a different email.', 'error')
            return render_template('admin_signup.html')
        if phone_number and User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered. Please login or use a different phone number.', 'error')
            return render_template('admin_signup.html')
        if employee_id and User.query.filter_by(employee_id=employee_id).first():
            flash('Employee ID already registered. Please use a different Employee ID.', 'error')
            return render_template('admin_signup.html')

        try:
            new_user = User(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                job_title=job_title,
                department=department,
                employee_id=employee_id
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            log_activity(new_user.id, new_user.email, 'Admin Signup', f'New admin user {new_user.full_name} ({new_user.email}) registered.')

            flash('Account created successfully! Please check your email for a welcome message.', 'success')
            return redirect(url_for('admin_login'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'error')
            return render_template('admin_signup.html')

    return render_template('admin_signup.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')

        user = User.query.filter_by(email=identifier).first()
        if not user and identifier.replace(' ', '').isdigit():
            user = User.query.filter_by(phone_number=identifier).first()

        if user and user.check_password(password):
            session['admin_logged_in'] = True
            session['admin_id'] = user.id
            session['admin_email'] = user.email
            session['admin_name'] = user.full_name
            flash('Login successful!', 'success')

            log_activity(user.id, user.email, 'Admin Login', f'Admin user {user.full_name} ({user.email}) logged in.')

            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            log_activity(None, identifier, 'Failed Login Attempt', f'Failed login attempt for identifier: {identifier}')
            return render_template('admin_login.html')

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to access the dashboard.', 'error')
        return redirect(url_for('admin_login'))

    admin_name = session.get('admin_name', 'Admin')

    # Calculate Total Users
    total_users = RegularUser.query.count()

    # Calculate Daily Logins (for today)
    today = datetime.utcnow().date()
    daily_logins = ActivityLog.query.filter(
        ActivityLog.action == 'User Login',
        func.date(ActivityLog.timestamp) == today.strftime('%Y-%m-%d') # Use func.date for SQLite
    ).count()

    # Calculate User Activity Over Time (e.g., last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    user_activity_over_time = db.session.query(
        func.date(ActivityLog.timestamp), # Use func.date for SQLite
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.action == 'User Login',
        ActivityLog.timestamp >= seven_days_ago,
        ActivityLog.timestamp.isnot(None) # Ensure timestamp is not null
    ).group_by(
        func.date(ActivityLog.timestamp)
    ).order_by(
        func.date(ActivityLog.timestamp)
    ).all()

    # Format data for chart (e.g., for a simple list or future JS chart)
    # func.date returns a string 'YYYY-MM-DD', so no need for .strftime('%Y-%m-%d') on the date part
    activity_data = []
    for date_str, count in user_activity_over_time:
        activity_data.append({'date': date_str, 'logins': count})

    # Get pending tickets (Problem Reports with status 'Open')
    pending_tickets = ProblemReport.query.filter_by(status='Open').count()

    # Get counts for content to review
    pending_testimonials_count = Testimonial.query.filter_by(approved=False).count()
    pending_blog_posts_count = BlogPost.query.filter_by(status='Pending').count()

    # Get recent activities for the "Recent Activities" section
    recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()


    return render_template(
        'admin_dashboard.html',
        admin_name=admin_name,
        total_users=total_users,
        daily_logins=daily_logins,
        user_activity_over_time=activity_data, # Pass formatted data
        pending_tickets=pending_tickets,
        pending_testimonials_count=pending_testimonials_count, # Pass new counts
        pending_blog_posts_count=pending_blog_posts_count,     # Pass new counts
        recent_activities=recent_activities # Pass recent activities to the template
    )

@app.route('/admin/onboarding', methods=['GET', 'POST'])
def admin_onboarding():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        business_name = request.form.get('business_name')
        contact_person = request.form.get('contact_person')
        contact_email = request.form.get('contact_email')
        phone_number = request.form.get('phone_number')
        industry = request.form.get('industry')
        notes = request.form.get('notes')

        if not all([business_name, contact_person, contact_email, industry]):
            flash('Please fill in all required fields for onboarding.', 'error')
            all_businesses = Business.query.all()
            return render_template('admin_onboarding.html', businesses=all_businesses)

        try:
            if Business.query.filter_by(contact_email=contact_email).first():
                flash('A business with this contact email is already registered.', 'error')
                all_businesses = Business.query.all()
                return render_template('admin_onboarding.html', businesses=all_businesses)

            new_business = Business(
                business_name=business_name,
                contact_person=contact_person,
                contact_email=contact_email,
                phone_number=phone_number,
                industry=industry,
                notes=notes
            )
            db.session.add(new_business)
            db.session.commit()

            admin_id = session.get('admin_id')
            admin_email = session.get('admin_email')
            log_activity(admin_id, admin_email, 'Business Onboarded', f'New business "{new_business.business_name}" onboarded by {admin_email}.')

            flash(f'Business "{business_name}" onboarding request submitted successfully!', 'success')
            return redirect(url_for('admin_onboarding'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during onboarding submission: {e}', 'error')
            admin_id = session.get('admin_id')
            admin_email = session.get('admin_email')
            log_activity(admin_id, admin_email, 'Business Onboarding Failed', f'Failed to onboard business "{business_name}". Error: {e}')
            all_businesses = Business.query.all()
            return render_template('admin_onboarding.html', businesses=all_businesses)

    all_businesses = Business.query.all()
    return render_template('admin_onboarding.html', businesses=all_businesses)

@app.route('/admin/logout')
def admin_logout():
    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    session.pop('admin_name', None)
    flash('You have been logged out.', 'info')

    log_activity(admin_id, admin_email, 'Admin Logout', f'Admin user {admin_email} logged out.')

    return redirect(url_for('admin_login'))

@app.route('/admin/logs')
def admin_logs():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('admin_login'))
    admin_name = session.get('admin_name', 'Admin')

    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template('admin_logs.html', logs=logs)

@app.route('/admin/user_details')
def admin_user_details():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('admin_login'))

    all_regular_users = RegularUser.query.all()
    admin_name = session.get('admin_name', 'Admin')

    return render_template('admin_user_details.html', users=all_regular_users, admin_name=admin_name)

@app.route('/admin/create_user', methods=['POST'])
def admin_create_user():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    full_name = request.form.get('full-name')
    email = request.form.get('email')
    phone_number = request.form.get('phone-number')
    state_of_origin = request.form.get('state-of-origin')
    lga = request.form.get('lga')
    residential_address = request.form.get('residential-address')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')

    errors = []

    if not all([full_name, email, phone_number, state_of_origin, lga, residential_address, password, confirm_password]):
        errors.append('All fields are required.')
    
    if password != confirm_password:
        errors.append('Passwords do not match.')

    password_regex = r"^(?=.*\d)(?=.*[!@#$%^&*()_+{}\[\]:;<>,.?~\\/-]).{8,}$"
    if not re.match(password_regex, password):
        errors.append('Password must be at least 8 characters long and include a number and a special character.')

    if RegularUser.query.filter_by(email=email).first():
        errors.append('Email already registered for a regular user.')

    if RegularUser.query.filter_by(phone_number=phone_number).first():
        errors.append('Phone number already registered for a regular user.')

    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('admin_user_details'))

    try:
        new_regular_user = RegularUser(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            state_of_origin=state_of_origin,
            lga=lga,
            residential_address=residential_address
        )
        new_regular_user.set_password(password)

        db.session.add(new_regular_user)
        db.session.commit()

        log_activity(admin_id, admin_email, 'Admin Created User', f'Admin {admin_email} created new regular user: {email}.')
        flash(f'User {full_name} created successfully!', 'success')
        return redirect(url_for('admin_user_details'))

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while creating the user: {e}', 'error')
        log_activity(admin_id, admin_email, 'Admin Create User Failed', f'Admin {admin_email} failed to create user {email}. Error: {e}')
        return redirect(url_for('admin_user_details'))

@app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
def admin_edit_user(user_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    user_to_edit = RegularUser.query.get(user_id)
    if not user_to_edit:
        flash('User not found.', 'error')
        log_activity(admin_id, admin_email, 'Admin Edit User Failed', f'Admin {admin_email} attempted to edit non-existent user with ID: {user_id}.')
        return redirect(url_for('admin_user_details'))

    full_name = request.form.get('full-name')
    email = request.form.get('email')
    phone_number = request.form.get('phone-number')
    state_of_origin = request.form.get('state-of-origin')
    lga = request.form.get('lga')
    residential_address = request.form.get('residential-address')
    new_password = request.form.get('password')
    confirm_new_password = request.form.get('confirm-password')

    errors = []

    if not all([full_name, email, phone_number, state_of_origin, lga, residential_address]):
        errors.append('All required fields must be filled.')

    if email != user_to_edit.email and RegularUser.query.filter_by(email=email).first():
        errors.append('This email is already registered to another user.')

    if phone_number != user_to_edit.phone_number and RegularUser.query.filter_by(phone_number=phone_number).first():
        errors.append('This phone number is already registered to another user.')

    if new_password:
        if new_password != confirm_new_password:
            errors.append('New passwords do not match.')
        
        password_regex = r"^(?=.*\d)(?=.*[!@#$%^&*()_+{}\[\]:;<>,.?~\\/-]).{8,}$"
        if not re.match(password_regex, new_password):
            errors.append('New password must be at least 8 characters long and include a number and a special character.')
    elif confirm_new_password:
        errors.append('Please provide a new password if you are confirming it.')

    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('admin_user_details'))

    try:
        user_to_edit.full_name = full_name
        user_to_edit.email = email
        user_to_edit.phone_number = phone_number
        user_to_edit.state_of_origin = state_of_origin
        user_to_edit.lga = lga
        user_to_edit.residential_address = residential_address

        if new_password:
            user_to_edit.set_password(new_password)

        db.session.commit()

        log_activity(admin_id, admin_email, 'Admin Edited User', f'Admin {admin_email} edited user: {user_to_edit.email}.')
        flash(f'User {user_to_edit.full_name} updated successfully!', 'success')
        return redirect(url_for('admin_user_details'))

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while updating the user: {e}', 'error')
        log_activity(admin_id, admin_email, 'Admin Edit User Failed', f'Admin {admin_email} failed to edit user {email}. Error: {e}')
        return redirect(url_for('admin_user_details'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    user_to_delete = RegularUser.query.get(user_id)
    if not user_to_delete:
        flash('User not found.', 'error')
        log_activity(admin_id, admin_email, 'Admin Delete User Failed', f'Admin {admin_email} attempted to delete non-existent user with ID: {user_id}.')
        return redirect(url_for('admin_user_details'))

    try:
        db.session.delete(user_to_delete)
        db.session.commit()

        log_activity(admin_id, admin_email, 'Admin Deleted User', f'Admin {admin_email} deleted user: {user_to_delete.email}.')
        flash(f'User {user_to_delete.full_name} deleted successfully!', 'success')
        return redirect(url_for('admin_user_details'))

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the user: {e}', 'error')
        log_activity(admin_id, admin_email, 'Admin Delete User Failed', f'Admin {admin_email} failed to delete user {user_to_delete.email}. Error: {e}')
        return redirect(url_for('admin_user_details'))


# --- User Login/Signup/Logout/Dashboard Routes ---
@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        full_name = request.form.get('full-name')
        email = request.form.get('email')
        phone_number = request.form.get('phone-number')
        state_of_origin = request.form.get('state-of-origin')
        lga = request.form.get('lga')
        residential_address = request.form.get('residential-address')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        profile_picture = request.files.get('profile-picture')

        errors = []

        if not all([full_name, email, phone_number, state_of_origin, lga, residential_address, password, confirm_password]):
            errors.append('Please fill in all required fields.')

        if password != confirm_password:
            errors.append('Passwords do not match.')

        if len(password) < 8 or not any(char.isdigit() for char in password) or \
           not any(char in "!@#$%^&*()_+{}[]:;<>,.?~\\/-" for char in password):
            errors.append('Password must be at least 8 characters long and include a number and a special character.')

        if RegularUser.query.filter_by(email=email).first():
            errors.append('Email already registered. Please login or use a different email.')

        if RegularUser.query.filter_by(phone_number=phone_number).first():
            errors.append('Phone number already registered. Please use a different phone number.')

        profile_picture_filename = None
        if profile_picture and profile_picture.filename != '':
            if allowed_file(profile_picture.filename):
                unique_filename = str(uuid.uuid4()) + '.' + profile_picture.filename.rsplit('.', 1)[1].lower()
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                profile_picture.save(filepath)
                profile_picture_filename = unique_filename
            else:
                errors.append('Invalid file type for profile picture. Only images (png, jpg, jpeg, gif) are allowed.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('user_signup.html',
                                   full_name=full_name, email=email, phone_number=phone_number,
                                   state_of_origin=state_of_origin, lga=lga, residential_address=residential_address)
        try:
            new_user = RegularUser(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                profile_picture_filename=profile_picture_filename,
                state_of_origin=state_of_origin,
                lga=lga,
                residential_address=residential_address
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully! You can now login.', 'success')
            return redirect(url_for('user_login'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'error')
            return render_template('user_signup.html',
                                   full_name=full_name, email=email, phone_number=phone_number,
                                   state_of_origin=state_of_origin, lga=lga, residential_address=residential_address)

    return render_template('user_signup.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')

        if not identifier or not password:
            flash('Please enter your email/phone and password.', 'error')
            log_activity(None, identifier, 'Failed User Login (Missing Credentials)', f'Missing credentials for identifier: {identifier}')
            return render_template('login.html')

        user = RegularUser.query.filter_by(email=identifier).first()
        if not user and identifier.replace(' ', '').replace('+', '').isdigit():
            user = RegularUser.query.filter_by(phone_number=identifier).first()

        if user and user.check_password(password):
            session['user_logged_in'] = True
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.full_name

            flash('Login successful!', 'success')
            log_activity(user.id, user.email, 'User Login', f'User {user.full_name} ({user.email}) logged in.')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            log_activity(None, identifier, 'Failed User Login (Invalid Credentials)', f'Invalid credentials for identifier: {identifier}')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_logged_in' not in session or not session['user_logged_in']:
        flash('Please login to access your dashboard.', 'error')
        return redirect(url_for('user_login'))

    user_id = session.get('user_id')
    user = RegularUser.query.get(user_id) # Fetch the full user object

    if not user:
        flash('User data not found. Please log in again.', 'error')
        return redirect(url_for('user_login'))

    # Fetch approved testimonials
    approved_testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.submitted_at.desc()).limit(5).all()
    # Fetch recent blog posts (e.g., status 'Published')
    recent_blog_posts = BlogPost.query.filter_by(status='Published').order_by(BlogPost.created_at.desc()).limit(5).all()

    return render_template('user_dashboard.html',
                           user=user,
                           approved_testimonials=approved_testimonials,
                           recent_blog_posts=recent_blog_posts)

@app.route('/user/edit_profile', methods=['GET', 'POST'])
def user_edit_profile():
    if 'user_logged_in' not in session or not session['user_logged_in']:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('user_login'))

    user_id = session.get('user_id')
    user = RegularUser.query.get(user_id)

    if not user:
        flash('User data not found. Please log in again.', 'error')
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        state_of_origin = request.form.get('state_of_origin')
        lga = request.form.get('lga')
        residential_address = request.form.get('residential_address')
        bio = request.form.get('bio')
        interests = request.form.getlist('interests') # getlist for multiple selections
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')
        profile_picture = request.files.get('profile_picture')

        errors = []

        # Basic validation for required fields (adjust as necessary)
        if not all([full_name, email, phone_number, state_of_origin, lga, residential_address]):
            errors.append('All fields marked with * are required.')

        # Check for unique email if changed
        if email and email != user.email and RegularUser.query.filter_by(email=email).first():
            errors.append('This email is already registered to another user.')
        
        # Check for unique phone number if changed
        if phone_number and phone_number != user.phone_number and RegularUser.query.filter_by(phone_number=phone_number).first():
            errors.append('This phone number is already registered to another user.')

        # Password validation
        if new_password:
            if new_password != confirm_new_password:
                errors.append('New passwords do not match.')
            password_regex = r"^(?=.*\d)(?=.*[!@#$%^&*()_+{}\[\]:;<>,.?~\\/-]).{8,}$"
            if not re.match(password_regex, new_password):
                errors.append('Password must be at least 8 characters long and include a number and a special character.')
        elif confirm_new_password: # If confirm_new_password is provided but new_password is not
            errors.append('Please provide a new password if you are confirming it.')

        # Profile picture upload
        if profile_picture and profile_picture.filename != '':
            if allowed_file(profile_picture.filename):
                unique_filename = str(uuid.uuid4()) + '.' + profile_picture.filename.rsplit('.', 1)[1].lower()
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                profile_picture.save(filepath)
                user.profile_picture_filename = unique_filename
            else:
                errors.append('Invalid file type for profile picture. Only images (png, jpg, jpeg, gif) are allowed.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('user_dashboard.html', user=user) # Re-render with existing data and errors

        try:
            user.full_name = full_name
            user.email = email
            user.phone_number = phone_number
            user.state_of_origin = state_of_origin
            user.lga = lga
            user.residential_address = residential_address
            user.bio = bio
            user.interests = ','.join(interests) # Store interests as a comma-separated string

            if new_password:
                user.set_password(new_password)

            db.session.commit()

            # Update session details if email/name changed
            session['user_email'] = user.email
            session['user_name'] = user.full_name

            log_activity(user.id, user.email, 'User Profile Updated', f'User {user.full_name} updated their profile.')
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating your profile: {e}', 'error')
            log_activity(user.id, user.email, 'User Profile Update Failed', f'User {user.full_name} failed to update profile. Error: {e}')
            return render_template('user_dashboard.html', user=user) # Re-render with existing data and errors

    # For GET request, just render the dashboard with user data
    return render_template('user_dashboard.html', user=user)


@app.route('/user/logout')
def user_logout():
    user_id = session.get('user_id')
    user_email = session.get('user_email')

    session.pop('user_logged_in', None)
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'info')

    log_activity(user_id, user_email, 'User Logout', f'User {user_email} logged out.')
    return redirect(url_for('user_login'))

@app.route('/user/report_problem', methods=['POST'])
def user_report_problem():
    if 'user_logged_in' not in session or not session['user_logged_in']:
        flash('Please login to report a problem.', 'error')
        return redirect(url_for('user_login'))

    user_id = session.get('user_id')
    user_email = session.get('user_email')
    user_name = session.get('user_name', 'User')

    subject = request.form.get('subject')
    description = request.form.get('description')

    if not subject or not description:
        flash('Subject and Description are required to report a problem.', 'error')
        log_activity(user_id, user_email, 'Problem Report Failed', 'User attempted to submit empty problem report.')
        return redirect(url_for('user_dashboard'))

    try:
        # Store in database
        new_report = ProblemReport(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            subject=subject,
            description=description
        )
        db.session.add(new_report)
        db.session.commit()

        # # Send email - COMMENTED OUT
        # msg = Message(
        #     subject=f"Problem Report from User: {user_name} ({user_email}) - {subject}",
        #     recipients=[app.config['MAIL_USERNAME']],
        #     body=f"User Name: {user_name}\nUser Email: {user_email}\n\nSubject: {subject}\n\nDescription:\n{description}"
        # )
        # mail.send(msg)

        flash('Your problem report has been sent successfully. We will get back to you shortly.', 'success')
        log_activity(user_id, user_email, 'Problem Reported', f'User reported a problem: {subject}.')
    except Exception as e:
        db.session.rollback() # Rollback database changes if email fails
        flash(f'Failed to send problem report. Please try again later. Error: {e}', 'error')
        log_activity(user_id, user_email, 'Problem Report Email Failed', f'Failed to send problem report email: {subject}. Error: {e}')

    return redirect(url_for('user_dashboard'))

@app.route('/user/contact_us', methods=['POST'])
def user_contact_us():
    if 'user_logged_in' not in session or not session['user_logged_in']:
        flash('Please login to contact us.', 'error')
        return redirect(url_for('user_login'))

    user_id = session.get('user_id')
    user_email = session.get('user_email')
    user_name = session.get('user_name', 'User')

    contact_name = request.form.get('name')
    contact_email = request.form.get('email')
    subject = request.form.get('subject')
    message_body = request.form.get('message')

    errors = []
    if not contact_name or not contact_email or not subject or not message_body:
        errors.append('All fields (Name, Email, Subject, Message) are required to contact us.')
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", contact_email):
        errors.append('Please enter a valid email address.')

    if errors:
        for error in errors:
            flash(error, 'error')
        log_activity(user_id, user_email, 'Contact Us Failed', 'User attempted to submit incomplete/invalid contact form.')
        return redirect(url_for('user_dashboard'))

    try:
        # Store in database
        new_message = ContactMessage(
            user_id=user_id,
            sender_name=contact_name,
            sender_email=contact_email,
            subject=subject,
            message_body=message_body
        )
        db.session.add(new_message)
        db.session.commit()

        # # Send email - COMMENTED OUT
        # msg = Message(
        #     subject=f"Contact Us Message from {contact_name} ({contact_email}) - {subject}",
        #     recipients=[app.config['MAIL_USERNAME']],
        #     body=f"From: {contact_name} <{contact_email}>\n\nSubject: {subject}\n\nMessage:\n{message_body}"
        # )
        # mail.send(msg)

        flash('Your message has been sent successfully. We will get back to you shortly.', 'success')
        log_activity(user_id, user_email, 'Contact Us Sent', f'User sent a contact message: {subject}.')
    except Exception as e:
        db.session.rollback() # Rollback database changes if email fails
        flash(f'Failed to send your message. Please try again later. Error: {e}', 'error')
        log_activity(user_id, user_email, 'Contact Us Email Failed', f'Failed to send contact message email: {subject}. Error: {e}')

    return redirect(url_for('user_dashboard'))

@app.route('/user/submit_testimonial', methods=['POST'])
def user_submit_testimonial():
    if 'user_logged_in' not in session or not session['user_logged_in']:
        flash('Please login to submit a testimonial.', 'error')
        return redirect(url_for('user_login'))

    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_email = session.get('user_email') # Get user email for sending
    testimonial_text = request.form.get('testimonial_text')

    if not testimonial_text:
        flash('Testimonial cannot be empty.', 'error')
        return redirect(url_for('user_dashboard'))

    try:
        new_testimonial = Testimonial(
            user_id=user_id,
            user_name=user_name,
            testimonial_text=testimonial_text
        )
        db.session.add(new_testimonial)
        db.session.commit()

        # Send email notification for new testimonial (commented out as requested)
        # try:
        #     msg = Message(
        #         subject=f"New Testimonial Submitted by {user_name}",
        #         recipients=[app.config['MAIL_USERNAME']], # Send to admin email
        #         body=f"A new testimonial has been submitted by {user_name} ({user_email}).\n\nTestimonial Content:\n{testimonial_text}\n\nPlease review and approve it in the admin dashboard."
        #     )
        #     mail.send(msg)
        #     log_activity(user_id, user_email, 'Testimonial Email Sent', f'Email notification sent for testimonial by {user_name}.')
        # except Exception as mail_e:
        #     print(f"Error sending testimonial notification email: {mail_e}")
        #     log_activity(user_id, user_email, 'Testimonial Email Failed', f'Failed to send email notification for testimonial by {user_name}. Error: {mail_e}')


        flash('Your testimonial has been submitted for review. Thank you!', 'success')
        log_activity(user_id, user_name, 'Testimonial Submitted', f'User {user_name} submitted a testimonial.')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while submitting your testimonial: {e}', 'error')
        log_activity(user_id, user_name, 'Testimonial Submission Failed', f'User {user_name} failed to submit testimonial. Error: {e}')

    return redirect(url_for('user_dashboard'))

@app.route('/user/create_blog_post', methods=['POST'])
def user_create_blog_post():
    if 'user_logged_in' not in session or not session['user_logged_in']:
        flash('Please login to create a blog post.', 'error')
        return redirect(url_for('user_login'))

    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_email = session.get('user_email') # Get user email for sending
    title = request.form.get('blog_title')
    content = request.form.get('blog_content')

    if not title or not content:
        flash('Blog post title and content cannot be empty.', 'error')
        return redirect(url_for('user_dashboard'))

    try:
        new_blog_post = BlogPost(
            user_id=user_id,
            user_name=user_name,
            title=title,
            content=content
        )
        db.session.add(new_blog_post)
        db.session.commit()

        # Send email notification for new blog post (commented out as requested)
        # try:
        #     msg = Message(
        #         subject=f"New Blog Post Submitted by {user_name}: {title}",
        #         recipients=[app.config['MAIL_USERNAME']], # Send to admin email
        #         body=f"A new blog post titled '{title}' has been submitted by {user_name} ({user_email}).\n\nContent Preview:\n{content[:200]}...\n\nPlease review and change its status in the admin dashboard."
        #     )
        #     mail.send(msg)
        #     log_activity(user_id, user_email, 'Blog Post Email Sent', f'Email notification sent for blog post "{title}" by {user_name}.')
        # except Exception as mail_e:
        #     print(f"Error sending blog post notification email: {mail_e}")
        #     log_activity(user_id, user_email, 'Blog Post Email Failed', f'Failed to send email notification for blog post "{title}" by {user_name}. Error: {mail_e}')


        flash('Your blog post has been submitted for review!', 'success')
        log_activity(user_id, user_name, 'Blog Post Created', f'User {user_name} created a blog post: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while creating your blog post: {e}', 'error')
        log_activity(user_id, user_name, 'Blog Post Creation Failed', f'User {user_name} failed to create blog post. Error: {e}')

    return redirect(url_for('user_dashboard'))

@app.route('/admin/communication_tools', methods=['GET'])
def admin_communication_tools():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('admin_login'))

    all_users = RegularUser.query.all()
    all_businesses = Business.query.all()

    # Fetch sent communication history from ActivityLog
    # Filter for actions related to communication sending
    sent_communications = ActivityLog.query.filter(
        ActivityLog.action.in_(['Mass Communication Sent Attempt', 'Notification Sent', 'Email Communication Sent'])
    ).order_by(ActivityLog.timestamp.desc()).all()

    return render_template('admin_communication.html',
                           all_users=all_users,
                           all_businesses=all_businesses,
                           sent_communications=sent_communications)


# Route for user to view all their notifications
@app.route('/user/notifications')
def user_notifications():
    if 'user_logged_in' not in session or not session['user_logged_in']:
        flash('Please login to view your notifications.', 'error')
        return redirect(url_for('user_login'))

    user_id = session.get('user_id')
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    return render_template('user_notifications.html', notifications=notifications)

# Route to mark a notification as read
@app.route('/user/mark_notification_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if 'user_logged_in' not in session or not session['user_logged_in']:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == session.get('user_id'):
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Notification not found or unauthorized'}), 404

@app.route('/admin/send_communication', methods=['POST'])
def admin_send_communication():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    recipient_type = request.form.get('recipient_type')
    selected_users = request.form.getlist('selected_users') # Will be a list of user IDs
    selected_businesses = request.form.getlist('selected_businesses') # Will be a list of business IDs
    message_type = request.form.get('message_type')
    subject = request.form.get('subject')
    message_content = request.form.get('message_content')

    # Basic validation
    if not recipient_type or not message_type or not message_content:
        flash('Please fill in all required communication fields.', 'error')
        return redirect(url_for('admin_communication_tools'))

    if message_type in ['email', 'notification'] and not subject:
        flash('Subject is required for Email and In-App Notifications.', 'error')
        return redirect(url_for('admin_communication_tools'))

    # Log the communication attempt (you would add actual sending logic here)
    details = f"Recipient Type: {recipient_type}, Message Type: {message_type}"
    if recipient_type == 'some-users':
        details += f", Users: {', '.join(selected_users)}"
    elif recipient_type == 'specific-businesses':
        details += f", Businesses: {', '.join(selected_businesses)}"
    details += f", Subject: {subject}, Content Preview: {message_content[:50]}..."

    log_activity(admin_id, admin_email, 'Mass Communication Sent Attempt', details)
    flash('Communication sent (or logged for sending) successfully!', 'success')

    # In a real application, you would iterate through selected_users/selected_businesses
    # and send the actual emails/SMS/notifications.
    # Example:
    # if recipient_type == 'all-users':
    #     users = RegularUser.query.all()
    #     for user in users:
    #         # send_email(user.email, subject, message_content)
    #         pass
    # elif recipient_type == 'some-users':
    #     users = RegularUser.query.filter(RegularUser.id.in_(selected_users)).all()
    #     for user in users:
    #         # send_email(user.email, subject, message_content)
    #         pass
    # ... and so on for other types and businesses

    return redirect(url_for('admin_communication_tools'))

@app.route('/admin/review_content')
def admin_review_content():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('admin_login'))

    admin_name = session.get('admin_name', 'Admin')
    pending_testimonials = Testimonial.query.filter_by(approved=False).order_by(Testimonial.submitted_at.asc()).all()
    pending_blog_posts = BlogPost.query.filter_by(status='Pending').order_by(BlogPost.created_at.asc()).all()

    return render_template('admin_review.html',
                           admin_name=admin_name,
                           pending_testimonials=pending_testimonials,
                           pending_blog_posts=pending_blog_posts)

@app.route('/admin/approve_testimonial/<int:testimonial_id>', methods=['POST'])
def admin_approve_testimonial(testimonial_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    testimonial = Testimonial.query.get(testimonial_id)
    if not testimonial:
        flash('Testimonial not found.', 'error')
        log_activity(admin_id, admin_email, 'Approve Testimonial Failed', f'Admin tried to approve non-existent testimonial ID: {testimonial_id}.')
        return redirect(url_for('admin_review_content'))

    try:
        testimonial.approved = True
        db.session.commit()
        flash('Testimonial approved successfully!', 'success')
        log_activity(admin_id, admin_email, 'Testimonial Approved', f'Admin approved testimonial ID: {testimonial_id} by {testimonial.user_name}.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving testimonial: {e}', 'error')
        log_activity(admin_id, admin_email, 'Approve Testimonial Failed', f'Error approving testimonial ID: {testimonial_id}. Error: {e}')

    return redirect(url_for('admin_review_content'))

@app.route('/admin/reject_testimonial/<int:testimonial_id>', methods=['POST'])
def admin_reject_testimonial(testimonial_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    testimonial = Testimonial.query.get(testimonial_id)
    if not testimonial:
        flash('Testimonial not found.', 'error')
        log_activity(admin_id, admin_email, 'Reject Testimonial Failed', f'Admin tried to reject non-existent testimonial ID: {testimonial_id}.')
        return redirect(url_for('admin_review_content'))

    try:
        db.session.delete(testimonial)
        db.session.commit()
        flash('Testimonial rejected and deleted successfully!', 'success')
        log_activity(admin_id, admin_email, 'Testimonial Rejected', f'Admin rejected and deleted testimonial ID: {testimonial_id} by {testimonial.user_name}.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting testimonial: {e}', 'error')
        log_activity(admin_id, admin_email, 'Reject Testimonial Failed', f'Error rejecting testimonial ID: {testimonial_id}. Error: {e}')

    return redirect(url_for('admin_review_content'))

@app.route('/admin/approve_blog_post/<int:post_id>', methods=['POST'])
def admin_approve_blog_post(post_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    blog_post = BlogPost.query.get(post_id)
    if not blog_post:
        flash('Blog post not found.', 'error')
        log_activity(admin_id, admin_email, 'Approve Blog Post Failed', f'Admin tried to approve non-existent blog post ID: {post_id}.')
        return redirect(url_for('admin_review_content'))

    try:
        blog_post.status = 'Published'
        db.session.commit()
        flash('Blog post published successfully!', 'success')
        log_activity(admin_id, admin_email, 'Blog Post Published', f'Admin published blog post ID: {post_id} titled "{blog_post.title}" by {blog_post.user_name}.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error publishing blog post: {e}', 'error')
        log_activity(admin_id, admin_email, 'Approve Blog Post Failed', f'Error publishing blog post ID: {post_id}. Error: {e}')

    return redirect(url_for('admin_review_content'))

@app.route('/admin/reject_blog_post/<int:post_id>', methods=['POST'])
def admin_reject_blog_post(post_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    blog_post = BlogPost.query.get(post_id)
    if not blog_post:
        flash('Blog post not found.', 'error')
        log_activity(admin_id, admin_email, 'Reject Blog Post Failed', f'Admin tried to reject non-existent blog post ID: {post_id}.')
        return redirect(url_for('admin_review_content'))

    try:
        db.session.delete(blog_post)
        db.session.commit()
        flash('Blog post rejected and deleted successfully!', 'success')
        log_activity(admin_id, admin_email, 'Blog Post Rejected', f'Admin rejected and deleted blog post ID: {post_id} titled "{blog_post.title}" by {blog_post.user_name}.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting blog post: {e}', 'error')
        log_activity(admin_id, admin_email, 'Reject Blog Post Failed', f'Error rejecting blog post ID: {post_id}. Error: {e}')

    return redirect(url_for('admin_review_content'))

# Route for all blog posts
@app.route('/user/blog_posts')
def user_all_blog_posts():
    # Fetch all published blog posts
    blog_posts = BlogPost.query.filter_by(status='Published').order_by(BlogPost.created_at.desc()).all()
    return render_template('all_blog_posts.html', blog_posts=blog_posts)



# Route for viewing a single blog post with comments (AJAX endpoint)
@app.route('/user/blog_post/<int:post_id>')
def view_blog_post(post_id):
    blog_post = BlogPost.query.get_or_404(post_id)
    # Fetch top-level comments (comments with no parent)
    comments = Comment.query.filter_by(blog_post_id=post_id, parent_comment_id=None).order_by(Comment.created_at.asc()).all()
    
    return render_template('single_blog_post_modal_content.html', blog_post=blog_post, comments=comments)

# Add route for submitting a comment (or reply)
@app.route('/user/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_logged_in' not in session or not session['user_logged_in']:
        flash('Please login to comment.', 'error')
        return redirect(url_for('user_login')) # Redirect to login if not logged in

    user_id = session.get('user_id')
    comment_text = request.form.get('comment_text')
    parent_comment_id = request.form.get('parent_comment_id') # Will be None for top-level comments

    if not comment_text:
        flash('Comment cannot be empty.', 'error')
        # Using request.referrer to redirect back to the page that initiated the request
        # This is more robust than hardcoding url_for('view_blog_post', post_id=post_id)
        return redirect(request.referrer or url_for('user_all_blog_posts'))

    try:
        new_comment = Comment(
            blog_post_id=post_id,
            user_id=user_id,
            comment_text=comment_text,
            parent_comment_id=parent_comment_id if parent_comment_id else None
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding comment: {e}', 'error')

    return redirect(request.referrer or url_for('user_all_blog_posts')) # Redirect back to the page that initiated the request



@app.route('/user/announcements')
def user_announcements():
    # Fetch only published announcements
    announcements = Announcement.query.filter_by(is_published=True).order_by(Announcement.created_at.desc()).all()
    return render_template('user_announcements.html', announcements=announcements)

@app.route('/user/opportunities')
def user_opportunities():
    # Fetch only published opportunities
    opportunities = Opportunity.query.filter_by(is_published=True).order_by(Opportunity.created_at.desc()).all()
    return render_template('user_opportunities.html', opportunities=opportunities)

@app.route('/user/resources')
def user_resources():
    # Fetch only published resources
    resources = Resource.query.filter_by(is_published=True).order_by(Resource.created_at.desc()).all()
    return render_template('user_resources.html', resources=resources)


# Route for all testimonials
@app.route('/user/testimonials')
def user_all_testimonials():
    # Fetch all approved testimonials
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.submitted_at.desc()).all()
    return render_template('all_testimonials.html', testimonials=testimonials)



# --- ADMIN CONTENT MANAGEMENT ROUTES ---

@app.route('/admin/content_management', methods=['GET','POST'])
def admin_content_management():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('admin_login'))

    admin_name = session.get('admin_name', 'Admin')

    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    opportunities = Opportunity.query.order_by(Opportunity.created_at.desc()).all()
    resources = Resource.query.order_by(Resource.created_at.desc()).all()

    return render_template('admin_content_management.html',
                           admin_name=admin_name,
                           announcements=announcements,
                           opportunities=opportunities,
                           resources=resources)

# Announcement Routes
@app.route('/admin/add_announcement', methods=['POST'])
def admin_add_announcement():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    title = request.form.get('title')
    content = request.form.get('content')
    is_published = request.form.get('is_published') == 'on' # Checkbox value

    if not title or not content:
        flash('Announcement title and content are required.', 'error')
        return redirect(url_for('admin_content_management'))

    try:
        new_announcement = Announcement(
            title=title,
            content=content,
            is_published=is_published
        )
        db.session.add(new_announcement)
        db.session.commit()
        flash('Announcement added successfully!', 'success')
        log_activity(admin_id, admin_email, 'Announcement Added', f'Admin added new announcement: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding announcement: {e}', 'error')
        log_activity(admin_id, admin_email, 'Announcement Add Failed', f'Failed to add announcement "{title}". Error: {e}')

    return redirect(url_for('admin_content_management'))

@app.route('/admin/edit_announcement/<int:announcement_id>', methods=['POST'])
def admin_edit_announcement(announcement_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        flash('Announcement not found.', 'error')
        log_activity(admin_id, admin_email, 'Edit Announcement Failed', f'Admin attempted to edit non-existent announcement ID: {announcement_id}.')
        return redirect(url_for('admin_content_management'))

    title = request.form.get('title')
    content = request.form.get('content')
    is_published = request.form.get('is_published') == 'on'

    if not title or not content:
        flash('Announcement title and content are required.', 'error')
        return redirect(url_for('admin_content_management'))

    try:
        announcement.title = title
        announcement.content = content
        announcement.is_published = is_published
        db.session.commit()
        flash('Announcement updated successfully!', 'success')
        log_activity(admin_id, admin_email, 'Announcement Edited', f'Admin edited announcement: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating announcement: {e}', 'error')
        log_activity(admin_id, admin_email, 'Announcement Edit Failed', f'Failed to edit announcement "{title}". Error: {e}')

    return redirect(url_for('admin_content_management'))

@app.route('/admin/delete_announcement/<int:announcement_id>', methods=['POST'])
def admin_delete_announcement(announcement_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        flash('Announcement not found.', 'error')
        log_activity(admin_id, admin_email, 'Delete Announcement Failed', f'Admin attempted to delete non-existent announcement ID: {announcement_id}.')
        return redirect(url_for('admin_content_management'))

    try:
        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement deleted successfully!', 'success')
        log_activity(admin_id, admin_email, 'Announcement Deleted', f'Admin deleted announcement: "{announcement.title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting announcement: {e}', 'error')
        log_activity(admin_id, admin_email, 'Announcement Delete Failed', f'Failed to delete announcement "{announcement.title}". Error: {e}')

    return redirect(url_for('admin_content_management'))

# Opportunity Routes
@app.route('/admin/add_opportunity', methods=['POST'])
def admin_add_opportunity():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    title = request.form.get('title')
    description = request.form.get('description')
    link = request.form.get('link')
    deadline_str = request.form.get('deadline')
    is_published = request.form.get('is_published') == 'on'

    if not title or not description:
        flash('Opportunity title and description are required.', 'error')
        return redirect(url_for('admin_content_management'))

    deadline = None
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid deadline format. Please use YYYY-MM-DDTHH:MM.', 'error')
            return redirect(url_for('admin_content_management'))

    try:
        new_opportunity = Opportunity(
            title=title,
            description=description,
            link=link,
            deadline=deadline,
            is_published=is_published
        )
        db.session.add(new_opportunity)
        db.session.commit()
        flash('Opportunity added successfully!', 'success')
        log_activity(admin_id, admin_email, 'Opportunity Added', f'Admin added new opportunity: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding opportunity: {e}', 'error')
        log_activity(admin_id, admin_email, 'Opportunity Add Failed', f'Failed to add opportunity "{title}". Error: {e}')

    return redirect(url_for('admin_content_management'))

@app.route('/admin/edit_opportunity/<int:opportunity_id>', methods=['POST'])
def admin_edit_opportunity(opportunity_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    opportunity = Opportunity.query.get(opportunity_id)
    if not opportunity:
        flash('Opportunity not found.', 'error')
        log_activity(admin_id, admin_email, 'Edit Opportunity Failed', f'Admin attempted to edit non-existent opportunity ID: {opportunity_id}.')
        return redirect(url_for('admin_content_management'))

    title = request.form.get('title')
    description = request.form.get('description')
    link = request.form.get('link')
    deadline_str = request.form.get('deadline')
    is_published = request.form.get('is_published') == 'on'

    if not title or not description:
        flash('Opportunity title and description are required.', 'error')
        return redirect(url_for('admin_content_management'))

    deadline = None
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid deadline format. Please use YYYY-MM-DDTHH:MM.', 'error')
            return redirect(url_for('admin_content_management'))

    try:
        opportunity.title = title
        opportunity.description = description
        opportunity.link = link
        opportunity.deadline = deadline
        opportunity.is_published = is_published
        db.session.commit()
        flash('Opportunity updated successfully!', 'success')
        log_activity(admin_id, admin_email, 'Opportunity Edited', f'Admin edited opportunity: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating opportunity: {e}', 'error')
        log_activity(admin_id, admin_email, 'Opportunity Edit Failed', f'Failed to edit opportunity "{title}". Error: {e}')

    return redirect(url_for('admin_content_management'))

@app.route('/admin/delete_opportunity/<int:opportunity_id>', methods=['POST'])
def admin_delete_opportunity(opportunity_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    opportunity = Opportunity.query.get(opportunity_id)
    if not opportunity:
        flash('Opportunity not found.', 'error')
        log_activity(admin_id, admin_email, 'Delete Opportunity Failed', f'Admin attempted to delete non-existent opportunity ID: {opportunity_id}.')
        return redirect(url_for('admin_content_management'))

    try:
        db.session.delete(opportunity)
        db.session.commit()
        flash('Opportunity deleted successfully!', 'success')
        log_activity(admin_id, admin_email, 'Opportunity Deleted', f'Admin deleted opportunity: "{opportunity.title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting opportunity: {e}', 'error')
        log_activity(admin_id, admin_email, 'Opportunity Delete Failed', f'Failed to delete opportunity "{opportunity.title}". Error: {e}')

    return redirect(url_for('admin_content_management'))

# Resource Routes
@app.route('/admin/add_resource', methods=['POST'])
def admin_add_resource():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    title = request.form.get('title')
    description = request.form.get('description')
    resource_type = request.form.get('resource_type')
    file_link = request.form.get('file_link')
    video_link = request.form.get('video_link')
    content = request.form.get('content')
    is_published = request.form.get('is_published') == 'on'

    if not title or not resource_type:
        flash('Resource title and type are required.', 'error')
        return redirect(url_for('admin_content_management'))

    # Basic validation based on resource type
    if resource_type == 'ebook' and not file_link:
        flash('File link is required for E-book resources.', 'error')
        return redirect(url_for('admin_content_management'))
    if resource_type == 'webinar' and not video_link:
        flash('Video link is required for Webinar resources.', 'error')
        return redirect(url_for('admin_content_management'))
    if resource_type == 'article' and not content:
        flash('Content is required for Article resources.', 'error')
        return redirect(url_for('admin_content_management'))
    if resource_type == 'toolkit' and not file_link:
        flash('File link is required for Toolkit resources.', 'error')
        return redirect(url_for('admin_content_management'))

    try:
        new_resource = Resource(
            title=title,
            description=description,
            resource_type=resource_type,
            file_link=file_link,
            video_link=video_link,
            content=content,
            is_published=is_published
        )
        db.session.add(new_resource)
        db.session.commit()
        flash('Resource added successfully!', 'success')
        log_activity(admin_id, admin_email, 'Resource Added', f'Admin added new {resource_type} resource: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding resource: {e}', 'error')
        log_activity(admin_id, admin_email, 'Resource Add Failed', f'Failed to add {resource_type} resource "{title}". Error: {e}')

    return redirect(url_for('admin_content_management'))

@app.route('/admin/edit_resource/<int:resource_id>', methods=['POST'])
def admin_edit_resource(resource_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    resource = Resource.query.get(resource_id)
    if not resource:
        flash('Resource not found.', 'error')
        log_activity(admin_id, admin_email, 'Edit Resource Failed', f'Admin attempted to edit non-existent resource ID: {resource_id}.')
        return redirect(url_for('admin_content_management'))

    title = request.form.get('title')
    description = request.form.get('description')
    resource_type = request.form.get('resource_type')
    file_link = request.form.get('file_link')
    video_link = request.form.get('video_link')
    content = request.form.get('content')
    is_published = request.form.get('is_published') == 'on'

    if not title or not resource_type:
        flash('Resource title and type are required.', 'error')
        return redirect(url_for('admin_content_management'))

    # Basic validation based on resource type
    if resource_type == 'ebook' and not file_link:
        flash('File link is required for E-book resources.', 'error')
        return redirect(url_for('admin_content_management'))
    if resource_type == 'webinar' and not video_link:
        flash('Video link is required for Webinar resources.', 'error')
        return redirect(url_for('admin_content_management'))
    if resource_type == 'article' and not content:
        flash('Content is required for Article resources.', 'error')
        return redirect(url_for('admin_content_management'))
    if resource_type == 'toolkit' and not file_link:
        flash('File link is required for Toolkit resources.', 'error')
        return redirect(url_for('admin_content_management'))

    try:
        resource.title = title
        resource.description = description
        resource.resource_type = resource_type
        resource.file_link = file_link
        resource.video_link = video_link
        resource.content = content
        resource.is_published = is_published
        db.session.commit()
        flash('Resource updated successfully!', 'success')
        log_activity(admin_id, admin_email, 'Resource Edited', f'Admin edited {resource.resource_type} resource: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating resource: {e}', 'error')
        log_activity(admin_id, admin_email, 'Resource Edit Failed', f'Failed to edit {resource.resource_type} resource "{title}". Error: {e}')

    return redirect(url_for('admin_content_management'))

@app.route('/admin/delete_resource/<int:resource_id>', methods=['POST'])
def admin_delete_resource(resource_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    resource = Resource.query.get(resource_id)
    if not resource:
        flash('Resource not found.', 'error')
        log_activity(admin_id, admin_email, 'Delete Resource Failed', f'Admin attempted to delete non-existent resource ID: {resource_id}.')
        return redirect(url_for('admin_content_management'))

    try:
        db.session.delete(resource)
        db.session.commit()
        flash('Resource deleted successfully!', 'success')
        log_activity(admin_id, admin_email, 'Resource Deleted', f'Admin deleted {resource.resource_type} resource: "{resource.title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting resource: {e}', 'error')
        log_activity(admin_id, admin_email, 'Resource Delete Failed', f'Failed to delete {resource.resource_type} resource "{resource.title}". Error: {e}')

    return redirect(url_for('admin_content_management'))




@app.route('/user/events')
def user_events():
    # Fetch only published events
    events = Event.query.filter_by(is_published=True).order_by(Event.event_date.desc()).all()
    return render_template('user_events.html', events=events)


# --- ADMIN EVENT MANAGEMENT ROUTES ---
@app.route('/admin/events', methods=['GET'])
def admin_events():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('admin_login'))
    
    admin_name = session.get('admin_name', 'Admin')
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('admin_events.html', admin_name=admin_name, events=events)

@app.route('/admin/add_event', methods=['POST'])
def admin_add_event():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    title = request.form.get('title')
    description = request.form.get('description')
    event_date_str = request.form.get('event_date')
    video_link = request.form.get('video_link')
    is_published = request.form.get('is_published') == 'on'
    image_file = request.files.get('image_file')

    if not title or not event_date_str:
        flash('Event title and date are required.', 'error')
        return redirect(url_for('admin_events'))

    try:
        event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid event date format. Please use YYYY-MM-DDTHH:MM.', 'error')
        return redirect(url_for('admin_events'))

    image_filename = None
    if image_file and image_file.filename != '':
        if allowed_event_image_file(image_file.filename):
            unique_filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['EVENT_IMAGE_UPLOAD_FOLDER'], unique_filename)
            image_file.save(filepath)
            image_filename = unique_filename
        else:
            flash('Invalid file type for event image. Only images (png, jpg, jpeg, gif) are allowed.', 'error')
            return redirect(url_for('admin_events'))

    try:
        new_event = Event(
            title=title,
            description=description,
            event_date=event_date,
            image_filename=image_filename,
            video_link=video_link,
            is_published=is_published
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Event added successfully!', 'success')
        log_activity(admin_id, admin_email, 'Event Added', f'Admin added new event: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding event: {e}', 'error')
        log_activity(admin_id, admin_email, 'Event Add Failed', f'Failed to add event "{title}". Error: {e}')

    return redirect(url_for('admin_events'))

@app.route('/admin/edit_event/<int:event_id>', methods=['POST'])
def admin_edit_event(event_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    event = Event.query.get(event_id)
    if not event:
        flash('Event not found.', 'error')
        log_activity(admin_id, admin_email, 'Edit Event Failed', f'Admin attempted to edit non-existent event ID: {event_id}.')
        return redirect(url_for('admin_events'))

    title = request.form.get('title')
    description = request.form.get('description')
    event_date_str = request.form.get('event_date')
    video_link = request.form.get('video_link')
    is_published = request.form.get('is_published') == 'on'
    image_file = request.files.get('image_file')
    remove_current_image = request.form.get('remove_current_image') == 'on'


    if not title or not event_date_str:
        flash('Event title and date are required.', 'error')
        return redirect(url_for('admin_events'))

    try:
        event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid event date format. Please use YYYY-MM-DDTHH:MM.', 'error')
        return redirect(url_for('admin_events'))

    # Handle image update/removal
    if remove_current_image and event.image_filename:
        # Delete old image file
        old_image_path = os.path.join(app.config['EVENT_IMAGE_UPLOAD_FOLDER'], event.image_filename)
        if os.path.exists(old_image_path):
            os.remove(old_image_path)
        event.image_filename = None
    
    if image_file and image_file.filename != '':
        if allowed_event_image_file(image_file.filename):
            # Delete old image if a new one is being uploaded
            if event.image_filename:
                old_image_path = os.path.join(app.config['EVENT_IMAGE_UPLOAD_FOLDER'], event.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            unique_filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['EVENT_IMAGE_UPLOAD_FOLDER'], unique_filename)
            image_file.save(filepath)
            event.image_filename = unique_filename
        else:
            flash('Invalid file type for event image. Only images (png, jpg, jpeg, gif) are allowed.', 'error')
            return redirect(url_for('admin_events'))

    try:
        event.title = title
        event.description = description
        event.event_date = event_date
        event.video_link = video_link
        event.is_published = is_published
        db.session.commit()
        flash('Event updated successfully!', 'success')
        log_activity(admin_id, admin_email, 'Event Edited', f'Admin edited event: "{title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating event: {e}', 'error')
        log_activity(admin_id, admin_email, 'Event Edit Failed', f'Failed to edit event "{title}". Error: {e}')

    return redirect(url_for('admin_events'))

@app.route('/admin/delete_event/<int:event_id>', methods=['POST'])
def admin_delete_event(event_id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        flash('Please login to perform this action.', 'error')
        return redirect(url_for('admin_login'))

    admin_id = session.get('admin_id')
    admin_email = session.get('admin_email')

    event = Event.query.get(event_id)
    if not event:
        flash('Event not found.', 'error')
        log_activity(admin_id, admin_email, 'Delete Event Failed', f'Admin attempted to delete non-existent event ID: {event_id}.')
        return redirect(url_for('admin_events'))

    try:
        # Delete associated image file if it exists
        if event.image_filename:
            image_path = os.path.join(app.config['EVENT_IMAGE_UPLOAD_FOLDER'], event.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!', 'success')
        log_activity(admin_id, admin_email, 'Event Deleted', f'Admin deleted event: "{event.title}".')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting event: {e}', 'error')
        log_activity(admin_id, admin_email, 'Event Delete Failed', f'Failed to delete event "{event.title}". Error: {e}')

    return redirect(url_for('admin_events'))




# --- Database Initialization ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
