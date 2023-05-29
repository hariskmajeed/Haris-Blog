from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, MetaData
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm
from forms import CreateRegisterForm
from forms import CommentForm
from flask_gravatar import Gravatar
from functools import wraps
from flask import abort
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
# engine = create_engine('sqlite:///blog.db', echo = True)
# meta = MetaData()

gravatar = Gravatar(app,
                    size=80,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

#CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, ForeignKey("user_db.id"))
    author = relationship("User", back_populates="posts")
    blog_authors = relationship("Comment", back_populates="blog_comments")



class User(UserMixin, db.Model):
    __tablename__ = "user_db"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="user_comments")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    user_comment = db.Column(db.String(250), nullable=False)
    comment_id = db.Column(db.Integer, ForeignKey("user_db.id"))
    blog_id = db.Column(db.Integer, ForeignKey("blog_posts.id"))
    user_comments = relationship("User", back_populates="comments")
    blog_comments = relationship("BlogPost", back_populates="blog_authors")


with app.app_context():
    db.create_all()



def admin_only(f):
    @wraps(f)
    def wrapper_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.is_authenticated:
            if current_user.id != 1:
                return abort(403)
                # Otherwise continue with the route function
            else:
                return f(*args, **kwargs)
        else:
            return abort(403)
    return wrapper_function





@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))

@app.route('/')
def get_all_posts():
    posts = db.session.query(BlogPost).all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        db_objects = db.session.query(User).all()
        if db_objects:
            for db_object in db_objects:
                if db_object.email == email:
                    flash("You've already signed up with that email, log in instead!")
                    return redirect(url_for('login'))
            user = User(
                email=email,
                password=password
            )
            db.session.add(user)
            db.session.commit()
            db_object = db.session.query(User).filter_by(email=email).first()
            login_user(db_object)

            return redirect(url_for('get_all_posts'))

        else:
            user = User(
                email=email,
                password=password
            )
            db.session.add(user)
            db.session.commit()
            db_object = db.session.query(User).filter_by(email=email).first()
            login_user(db_object)

            return redirect(url_for('get_all_posts'))


    form = CreateRegisterForm()
    return render_template("register.html", form=form, current_user=current_user)




@app.route('/login', methods=['GET', 'POST'])
def login():
    form = CreateRegisterForm()
    if form.validate_on_submit():
        db_obj = db.session.query(User).filter_by(email=request.form.get("email")).first()
        if db_obj:
            if db_obj.password == request.form.get("password"):
                login_user(db_obj)
                return redirect(url_for('get_all_posts'))
            else:
                flash("The password is not correct please try again")
                return redirect(url_for('login'))
        else:
            flash("The email Does not exist please try again")
            return redirect(url_for('login'))


    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
        comment = comment_form.comment.data
        new_comment = Comment(
            user_comment=comment,
            comment_id=current_user.id,
            blog_id=requested_post.id
        )
        db.session.add(new_comment)
        db.session.commit()
        return render_template("post.html", post=requested_post, current_user=current_user, comment=comment_form)
    return render_template("post.html", post=requested_post, current_user=current_user, comment=comment_form)


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>")
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
