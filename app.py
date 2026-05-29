from flask import Flask,render_template,redirect,url_for,request,flash
import os
import uuid
import markdown
import json
from ai import Ai_summary,Ai_FLASKCARD,Ai_Quiz
from datetime import datetime
from file_reader import File_Reader
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String,ForeignKey,Text
from sqlalchemy.orm import Mapped, mapped_column,relationship
from flask_login import LoginManager,login_required,current_user,login_user,logout_user,UserMixin
from werkzeug.security import generate_password_hash , check_password_hash
from collections import Counter
from dotenv import load_dotenv
load_dotenv()
class Base(DeclarativeBase):
  pass

login_manager = LoginManager()
db = SQLAlchemy(model_class=Base)
app=Flask(__name__)
app.config['SECRET_KEY']=os.getenv('SECRET_KEY')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))



class User(UserMixin,db.Model):
    __tablename__='users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True,nullable=False)
    username: Mapped[str] = mapped_column(nullable=False)
    password:Mapped[str]=mapped_column(nullable=False)
    upload=relationship('Upload',back_populates='owner')
    card=relationship('Flask_Card',back_populates='owner')
    quiz=relationship('Quiz',back_populates='owner')
class Upload(db.Model):
    __tablename__='uploads'
    id: Mapped[int] = mapped_column(primary_key=True)
    original_filename = mapped_column(String,nullable=False)
    saved_filename = mapped_column(String,nullable=False)
    file_type = mapped_column(String,nullable=False)
    upload_date = mapped_column(String,nullable=False)
    extracted_text = mapped_column(Text,nullable=False)
    summary_text = mapped_column(Text,nullable=True)
    user_id=mapped_column(ForeignKey('users.id'))
    owner=relationship('User',back_populates='upload')
    
    
class Flask_Card(db.Model):
    __tablename__='flaskcards'
    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    answer: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    upload_id: Mapped[int] = mapped_column(
        ForeignKey("uploads.id")
    )

    
    
    user_id=mapped_column(ForeignKey('users.id'))
    owner=relationship('User',back_populates='card')
    
    
class Quiz(db.Model):
    __tablename__='quizs'
    id: Mapped[int] = mapped_column(primary_key=True)
    score:Mapped[int]=mapped_column(Integer)
    created_at=mapped_column(String)
    total_quizs=mapped_column(Integer)
    user_id=mapped_column(ForeignKey('users.id'))
    upload_id=mapped_column(ForeignKey('uploads.id'))
    owner=relationship('User',back_populates='quiz')
    questions=relationship("QuizQuestion",back_populates='quiz')
    
class QuizQuestion(db.Model):
    __tablename__='quizquestions'
    id: Mapped[int] = mapped_column(primary_key=True)
    question :Mapped[str]=mapped_column(Text,nullable=False)
    option_a :Mapped[str]=mapped_column(String,nullable=False)
    option_b :Mapped[str]=mapped_column(String,nullable=False)
    option_c :Mapped[str]=mapped_column(String,nullable=False)
    option_d :Mapped[str]=mapped_column(String,nullable=False)
    correct_answer :Mapped[str]=mapped_column(String,nullable=False)
    quiz_id=mapped_column(ForeignKey('quizs.id'))
    quiz=relationship("Quiz",back_populates='questions')
    
    
with app.app_context():
    db.create_all()



@app.route("/")
def home():
    
        
    return render_template("index.html",login_user=login_user)


@app.route("/profile")
def profile():
    user=db.session.execute(db.select(User).where(User.id==current_user.id)).scalar()
    upload_count=len(db.session.execute(db.select(Upload).where(Upload.user_id == current_user.id)).scalars().all())
    flask_count=Flask_Card.query.filter_by(user_id=current_user.id).count()
    quizs=Quiz.query.filter_by(user_id=current_user.id)
    quiz_count=quizs.count()
    scores=sum([sco.score for sco in quizs])
    quizzes = db.session.execute(db.select(Quiz).where(Quiz.user_id == current_user.id)).scalars().all()
    avarage_score=0
    total_questions = sum(
        quiz.total_quizs for quiz in quizzes
    )

    if scores>0:
        avarage_score=(scores / total_questions)*100
    

    


    return render_template('profile.html',user=user,upload_count=upload_count,
                           flask_count=flask_count,
                           quiz_count=quiz_count,
                           avarage_score=avarage_score)



@app.route("/login",methods=["GET",'POST'])
def login():
    if request.method == "POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            flash("User not ragister")
        elif not check_password_hash(user.password,password):
            flash("Wrong passward try again")
        else:
            flash("login Seccessfully")
            login_user(user)
            return redirect (url_for('dashbord'))



        
    return render_template("login.html")



@app.route("/ragister",methods=["GET",'POST'])
def ragister():
    if request.method == "POST":
        user=request.form.get('name')
        email=request.form.get('email')
        password=generate_password_hash(password=request.form.get('password'),
                                        method="pbkdf2:sha256",
                                        salt_length=20)
        
        new_user=User(username=user,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))




    return render_template("ragister.html")


@app.route("/logout")
def log_out():
    logout_user()
    return redirect (url_for('home'))

@app.route("/dashbord")
@login_required
def dashbord():
    upload_count=Upload.query.filter_by(user_id=current_user.id).count()
    flaskcard_count=Flask_Card.query.filter_by(user_id=current_user.id).count()
    quiz_count=Quiz.query.filter_by(user_id=current_user.id).count()
    latest_upload = db.session.execute(
    db.select(Upload)
).scalar()
    upload_per_user=db.session.execute(db.select(Upload).where(Upload.user_id==current_user.id)).scalars().all()
    upload_date=[date.upload_date for date in upload_per_user]
    print(upload_date)
   
    counter = Counter(upload_date)
    chart_lable=list(counter.keys())
    chart_valu=list(counter.values())
    print(chart_lable)
    print(chart_valu)
    recent_uploads=db.session.execute(db.select(Upload).where(Upload.user_id==current_user.id).order_by(Upload.id.desc()).limit(5)).scalars().all()
    
    return render_template("dashbord.html",upload_count=upload_count,
                           flaskcard_count=flaskcard_count,
                           quiz_count=quiz_count,
                           latest_upload=latest_upload,
                           chart_lable=chart_lable,
                           chart_valu=chart_valu,
                           recent_uploads=recent_uploads

                           )




@app.route("/flaskcard/<int:id>", methods=['GET','POST'])
@login_required
def flaskcard(id):

    upload = db.session.execute(db.select(Upload).where(Upload.id==id,Upload.user_id==current_user.id)).scalar()


    if not upload:

        return "file not found"

    existing_cards = db.session.execute(

        db.select(Flask_Card).where(
            Flask_Card.upload_id == upload.id
        )

    ).scalars().all()

    if not existing_cards:
        if len(upload.extracted_text) >15000:
            flask_card = Ai_FLASKCARD(upload.summary_text)
            cards = json.loads(flask_card)
        else:
            flask_card = Ai_FLASKCARD(
                upload.extracted_text
            )

            cards = json.loads(flask_card)

        for card in cards:

            new_card = Flask_Card(

                question=card["question"],

                answer=card["answer"],

                upload_id=upload.id,
                user_id=current_user.id

            )

            db.session.add(new_card)

        db.session.commit()

    read = db.session.execute(

        db.select(Flask_Card).where(
            Flask_Card.upload_id == upload.id
        )

    ).scalars().all()

    return render_template(
        "flaskcard.html",
        cards=read
    )

@app.route("/scoreing/<int:upload_id>",methods=['GET','POST'])
def scoreing(upload_id):
    score=0
    if request.method == 'POST':
        user_dict=request.form
        for user_answer in user_dict:
            quiz_id=user_answer.split("_")[-1]
            currect_ans=db.session.execute(db.select(QuizQuestion).where(QuizQuestion.id==quiz_id)).scalar()
            print(user_dict[user_answer])
            if user_dict[user_answer] == currect_ans.correct_answer:
                
                score+=1
            percentage=int(round(score/len(user_dict)*100,2))
            quiz=db.session.execute(db.select(Quiz).where(Quiz.upload_id==upload_id,Quiz.user_id==current_user
                                                     .id)).scalar()
            quiz.score = score
            db.session.commit()
        return render_template('score.html',score=score,total=len(user_dict),percentage=percentage,upload_id=upload_id)

@app.route("/quiz/<int:id>",methods=["GET", "POST"])
@login_required
def quiz(id):
    
   
        upload = db.session.execute(db.select(Upload).where(Upload.id==id,Upload.user_id==current_user.id)).scalar()


        if not upload:
            return "Upload not found"

        # check if quiz already exists
        existing_quiz = db.session.execute(

            db.select(Quiz).where(
                Quiz.upload_id == upload.id,Quiz.user_id == current_user.id)).scalar()

        # create quiz only once
        if not existing_quiz:
            if upload.summary_text:


                source_text = upload.summary_text


            else:

                source_text = upload.extracted_text

            ai_quiz = Ai_Quiz(source_text)

            quiz_json = json.loads(ai_quiz)

            new_quiz = Quiz(
                score=0,
                user_id=current_user.id,
                upload_id=upload.id,
                created_at=datetime.now().strftime("%d %B %Y"),
                total_quizs=len(quiz_json)

            )

            db.session.add(new_quiz)

            db.session.commit()

            for q in quiz_json:
                print(q['correct_answer'])

                question = QuizQuestion(

                    question=q['question'],

                    option_a=q['option_a'],

                    option_b=q['option_b'],

                    option_c=q['option_c'],

                    option_d=q['option_d'],

                    correct_answer=q['correct_answer'],

                    quiz_id=new_quiz.id
                )

                db.session.add(question)

            db.session.commit()

            existing_quiz = new_quiz

        questions = db.session.execute(

            db.select(QuizQuestion).where(
                QuizQuestion.quiz_id == existing_quiz.id
            )

        ).scalars().all()

        return render_template(
            "quiz.html",
            quizs=questions,
            id=id
        )

@app.route("/quiz_history")
@login_required
def quiz_history():
    quizzes=db.session.execute(db.select(Quiz).where(Quiz.user_id==current_user.id)
                               .order_by(Quiz.id.desc())).scalars().all()
    return render_template('quiz_history.html',
                          quizzes=quizzes )



@app.route("/summaries")
@login_required
def summaries():

    uploads = db.session.execute(
        db.select(Upload).where(
            Upload.user_id == current_user.id
        )
    ).scalars()

    return render_template(
        "summaries.html",
        uploads=uploads
    )


@app.route("/summary/<int:upload_id>")
@login_required
def summary(upload_id):

    upload = db.session.execute(db.select(Upload).where(Upload.id==upload_id,Upload.user_id==current_user.id)).scalar()

    if not upload:

        return "Upload not found"
    if upload.summary_text:
        summary_text=upload.summary_text
    else:
        summary_text = Ai_summary(upload.extracted_text)
        upload.summary_text = summary_text

    db.session.commit()


    summary_html = markdown.markdown(summary_text)

    return render_template(
        "summary.html",
        summary=summary_html,
        upload_id=upload_id
    )
    





@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():

    if request.method == "POST":

        try:

            file = request.files.get('file')

            if not file:
                return "No file"

            new_id = uuid.uuid4()

            file_name = f"{new_id}_{file.filename}"

            filepath = f"static/files/{file_name}"

            file.save(filepath)

            name, extension = os.path.splitext(file.filename)

            upload_date = datetime.now().strftime("%d %B")

            reader = File_Reader(file_name)

            text = ""

            if extension == ".docx":

                text = reader.docx_reader()

            elif extension == ".pdf":

                text = reader.pdf_reader()

            elif extension in [".jpg", ".png"]:

                text = reader.screenshot_photo_reader()

            new_upload = Upload(
                original_filename=file.filename,
                saved_filename=file_name,
                file_type=extension,
                upload_date=upload_date,
                extracted_text=text,
                user_id=current_user.id
            )

            db.session.add(new_upload)

            db.session.commit()

            return redirect(
                url_for('notes', file=file_name)
            )

        except Exception as e:

            db.session.rollback()

            print(e)

            return str(e)

    return render_template("upload.html")
@app.route('/notes/<file>')
@login_required
def notes(file):

    upload = db.session.execute(
        db.select(Upload).where(
            Upload.saved_filename == file
        )
    ).scalar()

    return render_template(
        'page.html',
        extracted_text=upload.extracted_text,
        upload_id=upload.id
    )

@app.route("/delete_upload/<int:id>",methods=['GET','POST'])
def delete_upload(id):
    upload_id=id
    
    upload_delete=db.session.execute(db.select(Upload).where(Upload.id==upload_id, Upload.user_id==current_user.id )).scalar()
    if not upload_delete:
        return "upload not found"
    filepath = f"static/files/{upload_delete.saved_filename}"

    if os.path.exists(filepath):

        os.remove(filepath)
    flask_delete=db.session.execute(db.select(Flask_Card).where(Flask_Card.upload_id==upload_id , Flask_Card.user_id ==current_user.id)).scalars().all()
    for card in flask_delete:
        db.session.delete(card)


    quiz_delete=db.session.execute(db.select(Quiz).where(Quiz.upload_id==upload_id , Quiz.user_id ==current_user.id)).scalars().all()
    for quiz in quiz_delete:
        questions=db.session.execute(db.select(QuizQuestion).where(QuizQuestion.quiz_id==quiz.id)).scalars().all()

        for question in questions:
           db.session.delete(question) 
        db.session.delete(quiz)
    db.session.delete(upload_delete)
    db.session.commit()
    return redirect(url_for('summaries'))
    


    
    
    


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)