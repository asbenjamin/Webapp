import os #to make sure we grab correct file extensions .png etc
import secrets # to prevent collision of filenames for pics
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort 
from webapp import app, db, bcrypt, mail
from webapp.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm #import forms, create instance in our route, pass it in to templates.htmls
from webapp.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

#posts = [{'author': 'Shammah','title': 'Blog post 1','content': 'First blog post','date_posted':'April 20, 2020'},
#'author': 'Maria','title': 'Blog post 2','content': 'Second blog post','date_posted':'April 21, 2020'}]

@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=4)
    return render_template('home.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route("/register", methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created, you can now login', 'success') #f string for .format and success is a bootstrap class
        return redirect(url_for('login'))   #refer to top of layout.html-with messages...
    return render_template('register.html', title='Register', form=form)

@app.route("/login" , methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next') # get returns either arument or none, rather than conventional arg dict
            return redirect (next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful, Please check email and password', 'danger') #danger is a bootstrap category and is red
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename) #underscore is 4 when you dont wana use a variable
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn) #L7: 31mINs
    
    output_size = (123,125)
    i = Image.open(form_picture) #this code resizes pics to save space on server
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['POST', 'GET'])
@login_required #we now need to tell our login route is located, go to init below login manager
def account():
    form= UpdateAccountForm()
    if form.validate():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit()
        flash('your account has been updated', 'success')
        return redirect(url_for('account')) #this causes browser to send a Get request! ...because of the Post-Get redirect pattern, (seen this be4? are you sure.... data will be resubmitted.....)
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email    
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)  #you can use f string alternative to concatenate(+)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.route("/post/new", methods=['POST', 'GET'])
@login_required
def new_post():
    form = PostForm()
    if form.validate():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')


@app.route("/post/<int:post_id>") #refers to template in post.html
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['POST', 'GET'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash ('Your post has been updated', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET': #find out more about get and post
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash ('Your post has been deleted', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=4)
    return render_template('user_posts.html', posts=posts, user=user)

def send_reset_email(user):
    token = user.get_reset_token()    
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'''To reser your password, click the following link:
    {url_for('reset_token', token=token, _external=True)}

    If you did not make this request, simply ignore this email and no changes will be made
    '''

    mail.send(msg)

@app.route("/reset_password", methods=['POST', 'GET'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['POST', 'GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None: #or if not user
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated, you can now login', 'success') #f string for .format and success is a bootstrap class
        return redirect(url_for('login'))  
    return render_template('reset_token.html', title='Reset Password', form=form)