import io
from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, flash, url_for, send_file, Response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
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


file_tags = db.Table('file_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'), primary_key=True)
)


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200))
    data = db.Column(db.LargeBinary)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.relationship('Tag', secondary=file_tags, lazy='subquery',
        backref=db.backref('files', lazy=True))  


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50), default='user')
    files = db.relationship('File', backref='user', lazy=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.drop_all()
    db.create_all()
    tags = ['animal', 'mountains', 'funny', 'nature', 'food', 'travel']
    for tag_name in tags:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('123456'), role='admin')
        db.session.add(admin)
    db.session.commit()
    

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    files = File.query.order_by(File.upload_time.desc()).all()
    file_data = []
    for file in files:
        title = file.title
        tags = [tag.name for tag in file.tags]
        username = file.user.username
        upload_time = file.upload_time
        file_data.append({
            'file': file,
            'title': title,
            'tags': tags,
            'username': username,
            'upload_time': upload_time.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return render_template('home.html', file_data=file_data, user=current_user, tags=Tag.query.all())

@app.route('/admin_home')
@login_required
def admin_home():
    if current_user.role != 'admin':
        abort(403)
    files = File.query.order_by(File.upload_time.desc()).all()
    file_data = []
    for file in files:
        title = file.title
        tags = [tag.name for tag in file.tags]
        username = file.user.username
        upload_time = file.upload_time
        file_data.append({
            'file': file,
            'title': title,
            'tags': tags,
            'username': username,
            'upload_time': upload_time.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return render_template('admin_home.html', file_data=file_data, user=current_user, tags=Tag.query.all())

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

        if 'login' in request.form:
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=remember)
                flash('Login successful')
                if user.role == 'admin':
                    return redirect(url_for('admin_home'))
                else:
                    return redirect(url_for('home'))
            else:
                flash('Invalid username or password')
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
    return render_template('post.html',user=current_user, tags=Tag.query.all())

@app.route('/uploads', methods=['POST'])
@login_required
def uploads():
    if request.method == 'POST':
        file = request.files['file']
        title = request.form.get('title')
        tags = request.form.getlist('tags')
        if file:
            filename = file.filename
            file_data = file.read()
            new_file = File(filename=filename, title=title, data=file_data, user_id=current_user.id)
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if tag:
                    new_file.tags.append(tag)
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

@app.route('/change_image_title/<int:file_id>', methods=['POST'])
@login_required
def change_image_title(file_id):
    new_title = request.form.get('newTitle')
    if not new_title:
        flash('New title is required')
        return redirect(url_for('my_posts'))
    file = File.query.get(file_id)
    if file.user_id != current_user.id:
        abort(403)
    file.title = new_title
    db.session.commit()
    return redirect(url_for('my_posts'))

@app.route('/delete_image/<int:file_id>', methods=['POST'])
@login_required
def delete_image(file_id):
    file = File.query.get(file_id)
    if file is None:
        abort(404)
    if file.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    db.session.delete(file)
    db.session.commit()
    return redirect(url_for('my_posts'))

@app.route('/tag/<tag_name>')
def get_images_by_tag(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    files = tag.files
    file_data = []
    for file in files:
        file_data.append({
            'id': file.id,
            'url': url_for('uploaded_file', file_id=file.id),
            'filename': file.filename,
            'upload_time': file.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
            'username': file.user.username,
        })

    return jsonify(file_data)

@app.route('/my_posts')
@login_required
def my_posts():
    files = File.query.filter_by(user_id=current_user.id).order_by(File.upload_time.desc()).all()
    file_data = []
    for file in files:
        title = file.title
        tags = [tag.name for tag in file.tags]
        username = file.user.username
        upload_time = file.upload_time
        file_data.append({
            'file': file,
            'title': title,
            'tags': tags,
            'username': username,
            'upload_time': upload_time.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return render_template('profile.html', file_data=file_data, user=current_user, tags=Tag.query.all())

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
