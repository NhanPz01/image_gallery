import io
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, flash, url_for, send_file, Response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.urandom(24)

# Initialize SQLAlchemy and LoginManager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the association table
file_tags = db.Table('file_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'), primary_key=True)
)

# Define the File class
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    data = db.Column(db.LargeBinary)  # New field to store binary data
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  
    tags = db.relationship('Tag', secondary=file_tags, lazy='subquery',
        backref=db.backref('files', lazy=True))  

# Define the Tag class
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# Define the User class
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    files = db.relationship('File', backref='user', lazy=True)  # New field

# User loader for LoginManager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database and create initial tags
with app.app_context():
    db.drop_all()
    db.create_all()
    tags = ['animal', 'mountains', 'funny', 'nature', 'food', 'travel']
    for tag_name in tags:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
    db.session.commit()
    
# Define routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    files = File.query.all()
    return render_template('home.html', files=files, user=current_user, tags=Tag.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        email = request.form.get('email')
        if email:
            user = User.query.filter_by(email=email).first()
        else:
            flash('Email is required')
            return redirect(url_for('login'))

        if 'register' in request.form:
            if user:
                flash('Username already exists')
                return redirect(url_for('login'))
            else:
                new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful')
                return redirect(url_for('home'))

        elif 'login' in request.form:
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=remember)
                flash('Login successful')
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password')
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/get_images_list')
def get_images_list():
    uploads_dir = app.config['UPLOAD_FOLDER']
    images_list = [f for f in os.listdir(
        uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
    return jsonify(images_list)

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    # Your code here
    return render_template('post.html',user=current_user, tags=Tag.query.all())

@app.route('/uploads', methods=['POST'])
@login_required
def uploads():
    if request.method == 'POST':
        file = request.files['file']
        tags = request.form.getlist('tags')  # Get the list of tags from the form data
        if file:
            filename = file.filename
            file_data = file.read()
            new_file = File(filename=filename, data=file_data, user_id=current_user.id)
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if tag:
                    new_file.tags.append(tag)  # Associate the tag with the file
            db.session.add(new_file)
            db.session.commit()
            return redirect('/home')
    return 'something wrong please try again!'

@app.route('/uploaded_file/<int:file_id>')
def uploaded_file(file_id):
    file = File.query.get_or_404(file_id)
    response = Response(file.data, mimetype="image/jpeg")
    response.headers.set('Content-Disposition', 'attachment', filename=file.filename)
    return response

@app.route('/download/<int:file_id>')
def download(file_id):
    file = File.query.get_or_404(file_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename, as_attachment=True)

@app.route('/delete/<int:file_id>')
def delete(file_id):
    file = File.query.get_or_404(file_id)
    filename = file.filename

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.remove(file_path)
    db.session.delete(file)
    db.session.commit()
    return redirect('/home')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
