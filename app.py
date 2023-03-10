import os,json,markdown, pandas as pd
import os.path as op
from datetime import *
from pytz import timezone
uae = timezone('Asia/Dubai')
from collections import defaultdict

from flask import Flask,render_template,request, redirect,url_for,Response,jsonify,flash,send_file,session
from flask_sqlalchemy import SQLAlchemy
from flask_qrcode import QRcode
from flask_login import LoginManager,login_required, login_user,logout_user,current_user
from flask_admin import Admin
# Enable File Upload in Admin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_mail import Mail,Message

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.inspection import inspect
from sqlalchemy import extract,func,desc

from data_processing import predict_with_ml

from app_word_cookies import *
from app_typoglycemia import *
from app_moon_phase_calculator import *
from app_qr_code_generator import *

from forms import *

from bs4 import BeautifulSoup

getcwd = os.getcwd()

if 'home' in getcwd:
    getcwd += '/mysite'

with open(getcwd+'/'+'quiz.json') as file:
    quizapp = json.load(file)

# Generates a Quiz Link if a quiz exists for the course
def quiz_exists(cname):

    quiz_link = False
    try:
        quizapp[cname]
    except:
        pass
    else:
        quiz_link = True

    return quiz_link


page_title = 'Vinsys - Course Content'

app = Flask(__name__, static_url_path='/static')

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "client.db"))

app.config['SECRET_KEY'] = 'eibfs2023Jan'
app.config['SQLALCHEMY_DATABASE_URI'] = database_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# set optional bootswatch theme - bootswatch.com/3/
app.config['FLASK_ADMIN_SWATCH'] = 'sandstone'

# Configuration for mail relay
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'bytesizetrainings@gmail.com'
app.config['MAIL_PASSWORD'] = 'npmtpbmxksmfwdaq'
app.config['MAIL_DEFAULT_SENDER'] = 'bytesizetrainings@gmail.com'

db = SQLAlchemy(app)
qrcode = QRcode(app)
mail = Mail(app)

from models import *

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
# since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

admin = Admin(app,index_view=MainAdminIndexView(),template_mode='bootstrap3')
admin.add_view(AllModelView(User,db.session))

admin.add_view(AllModelView(Course,db.session,category="Course"))
admin.add_view(LessonView(Lesson,db.session,category="Course"))
admin.add_view(AllModelView(UserCourse,db.session,category="Course"))

admin.add_view(AssignmentView(CourseAssignment,db.session,category="Assignment"))
admin.add_view(AllModelView(CourseAssignmentSubscription,db.session,category="Assignment"))
admin.add_view(AllModelView(CourseAssignmentSent,db.session,category="Assignment"))

admin.add_view(AllModelView(Activity,db.session))

# Add a Custom Page to Admin
admin.add_view(LessonOrderView(name='Lesson Order', endpoint='lesson_order',category="Course"))

path = op.join(op.dirname(__file__), 'static')
admin.add_view(FileAdmin(path, '/static/images/', name='Images'))

def cas_check(id):

    student = db.session.query(Student).filter(Student.studentName == session['student']).first()
    cas = db.session.query(CourseAssignmentSubscription)\
        .filter(CourseAssignmentSubscription.courseId == id,\
            CourseAssignmentSubscription.studentId == student.id).first()

    return cas,student

def send_assignment(course,student,cas):

    # check the history of sent assignment
    assignmentSent = CourseAssignmentSent.query\
        .filter(CourseAssignmentSent.courseId == course.id,\
            CourseAssignmentSent.studentId == student.id,\
            CourseAssignmentSent.assignmentOrderNo == cas.assignmentOrderNo).all()

    # send the assignment if not previously sent
    if not assignmentSent:
        assignment = CourseAssignment.query.filter(CourseAssignment.courseId == course.id).first()
        html = markdown.markdown(assignment.assignmentDescription)

        msg_bg = Message(f"{course.courseName} - Assignment {cas.assignmentOrderNo}",recipients=[student.email],sender=('Sunil Nair', 'boardgameschedulers@gmail.com'))
        msg_bg.html = f'''
                <p>Dear {student.studentName},</p>
                <span>Please find below instructions for your assignment.</span>

                <h3>{assignment.assignmentTitle}</h3>
                {html}
            '''
        if assignment.file_url:
            msg_bg.html += f'''
                <h4><a href='{assignment.file_url}'>Download Exercise File</a></h4>
            '''
        msg_bg.html += f'''
        <span>Thank You</span><br/>
        <span><b>Sunil Nair</b></span>
            '''

        try:
            mail.send(msg_bg)
        except:
            flash("Sorry, request is unsucessful. Please contact Game Admins",'error')
        else:
            app.logger.info(f'{datetime.now()} - Email sent - {student.studentName} - {student.email} - Course:{course.courseName} - Assignment:{assignment.assignmentTitle}',)

            # Update CourseAssignmentSent to maintain a log of emails sent
            ca_sent = CourseAssignmentSent()
            ca_sent.courseId = course.id
            ca_sent.studentId = student.id
            ca_sent.assignmentOrderNo = cas.assignmentOrderNo
            ca_sent.sent_dt = datetime.now(uae)

            db.session.add(ca_sent)

            # Increment the Order Number in CourseAssignmentSubscription based on whats been sent
            cas = CourseAssignmentSubscription.query\
                .filter(CourseAssignmentSubscription.courseId==course.id,\
                    CourseAssignmentSubscription.studentId==student.id
                ).first()
            cas.assignmentOrderNo += 1

            db.session.commit()

@app.route('/login',methods=['GET','POST'])
def login():

    title = "Login"

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(username=form.username.data).first()

        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, form.password.data):
            flash('Please check your login details and try again.')
            return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page

        # if the above check passes, then we know the user has the right credentials
        login_user(user,remember=form.remember.data)
        return redirect(url_for('index'))

    return render_template('login.html',title = title,form=form)

@app.route('/signup')
def signup():
    title = "Sign Up"
    form = SignupForm()
    return render_template('signup.html',form=form,logo="/static/images/company_logo.png")

@app.route('/signup',methods=['POST'])
def signup_post():

    form = SignupForm()

    if form.validate_on_submit():

        user = User.query.filter_by(username=form.username.data).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Username already exists')
            return redirect(url_for('signup'))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(username=form.username.data, password=generate_password_hash(form.password.data, method='sha256'))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # code to validate and add user to database goes here
        return redirect(url_for('login'))

    return render_template(url_for('signup'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404


@app.route('/',methods=['GET','POST'])
@login_required
def index():

    courses = Course.query.all()

    if request.method == 'POST':

        def name_check(x):
            if len(x) < 10:
                flash("Please provide your fullname")
                return False

            if any(chr.isdigit() for chr in x):
                flash("Please provide your correct name")
                return False

            return x.strip().title()

        if name_check(request.form["name"]):
            session["student"] = name_check(request.form["name"])
        else:
            return redirect(url_for('index'))

        # Add New Student to Database
        check_student = db.session.query(Student).\
            filter(Student.studentName == session["student"]).all()

        if not check_student:
            student = Student()
            student.studentName = session["student"]

            db.session.add(student)
            db.session.commit()


    if "student" not in session:
        return render_template("register.html",
        courses=courses,
        logo="/static/images/company_logo.png")

    courses = db.session.query(Course).\
            filter(UserCourse.userId == current_user.id,\
                Course.id == UserCourse.courseId).all()

    return render_template("courses.html",
    courses = courses,
    logo="/static/images/company_logo.png",
    title=page_title)


@app.route('/course/<int:id>',methods=['GET','POST'])
@login_required
def course(id):

    session["course"] = id

    course = Course.query.get_or_404(id)

    # Check if Student has already subscribed to the Course Assignments
    cas,student = cas_check(id)

    html = markdown.markdown(course.courseDescription)

    lessons = db.session.query(Lesson)\
        .join(Course, Course.id == Lesson.courseId)\
        .filter(Course.id == id)\
        .order_by(Lesson.lessonOrder).all()

    # Form Submission for Assignment Subscription
    if request.method == 'POST':
        student.email = request.form["email"]

        # Have to check if there is an old subscription
        # if exists, update with 1 or else create new



        if cas:
            if not cas.subscription:
                cas.subscription = 1
                db.session.commit()
        else:
            new_cas = CourseAssignmentSubscription()
            new_cas.courseId = session["course"]
            new_cas.studentId = student.id
            new_cas.assignmentOrderNo = 1
            new_cas.subscription = 1

            db.session.add(new_cas)
            db.session.commit()

            send_assignment(course,student,new_cas)

        cas = cas_check(session["course"])[0]

    return render_template("course.html",
    lessons = lessons, course = course,
    html = html,cas = cas,
    quiz_link = quiz_exists(course.courseName),
    logo='/static/images/company_logo.png',
    title = course.courseName)

@app.route("/unsubscribe",methods=["GET","POST"])
def unsubscribe():

    student = db.session.query(Student).filter(Student.studentName == session['student']).first()

    cas = CourseAssignmentSubscription.query.filter(CourseAssignmentSubscription.courseId==session["course"],\
        CourseAssignmentSubscription.studentId==student.id).first()

    cas.subscription = 0

    db.session.commit()

    return redirect(url_for("course",id=session["course"]))

@app.route('/view_lesson/<int:id>',methods=['GET','POST'])
@login_required
def viewlesson(id):


    lesson = Lesson.query.get_or_404(id)
    course = Course.query.get_or_404(lesson.courseId)
    # courseid = lesson.courseId

    lessons = db.session.query(Lesson)\
        .join(Course, Course.id == Lesson.courseId)\
        .filter(Course.id == course.id)\
        .order_by(Lesson.lessonOrder).all()
    
    soup = BeautifulSoup(lesson.lessonDescription, 'html.parser')

    # Find all h2 headings for ToC
    h2s = [h2.text.strip() for h2 in soup.find_all('h2')]
    print(h2s)
        

    session["lessonNM"] = lesson.lessonName

    html = markdown.markdown(lesson.lessonDescription)

    return render_template("view_lesson.html",
    course = course, lesson = lesson,lessons = lessons,html = html,
    h2s=h2s,
    quiz_link=quiz_exists(course.courseName),
    title = lesson.lessonName,
    logo='/static/images/company_logo.png')

@app.route('/lesson_order/',methods=['GET','POST'])
@login_required
def lesson_order():
    if current_user.username == 'sunil.nair':
        courses = db.session.query(Course).all()


        if request.method == 'POST':
            lesson_dict = request.form
            for x in list(request.form):
                lesson = Lesson.query.filter(Lesson.id == int(x)).first()
                lesson.lessonOrder = int(lesson_dict.getlist(x)[0])

                db.session.commit()

            return redirect(url_for('lesson_order'))
        return render_template('lesson_order.html',courses = courses)

    else:
        return redirect(url_for('index'))

@app.route('/admin/extract_lessons')
def extract_lessons():
    lessons = list()

    if request.args.get('q'):
        course_id = int(request.args.get('q'))

        lesson_ = db.session.query(Lesson).\
            filter(Lesson.courseId == course_id).\
                order_by(Lesson.lessonOrder).all()


        for lesson in lesson_:

            lessons.append(
                {
                            "id":lesson.id,
                            "lessonName":lesson.lessonName,
                            "lessonOrder":lesson.lessonOrder
                })

    return jsonify(lessons = lessons)


@app.route('/quiz_results',methods=['GET','POST'])
@login_required
def quiz_results():
    course = Course.query.get_or_404(session['course'])

    year = datetime.now(uae).year
    month = datetime.now(uae).month
    day = datetime.now(uae).day

    quiz_results = db.session.query(Student.studentName,\
    func.sum(QuizResults.response).label('score'),\
    func.count(QuizResults.response).label('questions'))\
                .filter(QuizResults.student_id == Student.id,\
                    extract('year', QuizResults.created_dt) == year,\
                    extract('month', QuizResults.created_dt) == month,\
                    extract('day', QuizResults.created_dt) == day,\
                    Student.studentName != 'Demo')\
                 .order_by(desc(func.sum(QuizResults.response)))\
                 .group_by(Student.studentName).all()

    return render_template("quiz/quiz_results.html",quiz_results = quiz_results,logo='/static/images/company_logo.png')

@app.route('/select_quiz',methods=['GET','POST'])
@login_required
def select_quiz():
    user_id = current_user.id
    courses = db.session.query(Course).\
        filter(Course.id == UserCourse.courseId,\
            UserCourse.userId == user_id).all()

    # Display only those courses which have a quiz in the json file
    courses = [course for course in courses if course.courseName in list(quizapp.keys())]

    if request.method == 'POST':
        session["course"] = int(request.form["selected_course"])

        return redirect(url_for('quiz'))

    return render_template('quiz/select_quiz.html',courses = courses)


@app.route('/quiz',methods=['GET','POST'])
@login_required
def quiz():

    course = Course.query.get_or_404(session["course"])

    year = datetime.now(uae).year
    month = datetime.now(uae).month
    day = datetime.now(uae).day

    check = ''
    quiz_responses = ''
    percentage = float()

    # Stores all questions, choice and correct answer
    # we use index[0] to extract the list from the dictionary
    session["quiz"] = [{theme:questions} for (theme,questions) in quizapp.items() if theme == course.courseName][0]


    # Current Question

    session["total_quiz"] = len(session["quiz"][course.courseName])

    # Select all Quiz Responses
    quiz_responses = db.session.query(QuizResults.response,QuizMaster.question)\
                .filter(Student.studentName == session["student"],\
                    QuizResults.student_id == Student.id,\
                    QuizResults.course_id == course.id,\
                    QuizMaster.id == QuizResults.question_id,\
                    extract('year', QuizResults.created_dt) == year,\
                    extract('month', QuizResults.created_dt) == month,\
                    extract('day', QuizResults.created_dt) == day).all()

    # If all the quiz responses have been posted, forward to results
    if session["total_quiz"] == len(quiz_responses):
        return render_template("quiz/end_quiz.html",quiz_responses = quiz_responses,logo='/static/images/company_logo.png')

    if request.method == 'POST':

        quiz_answer = request.form["given_answer"]

        check = db.session.query(QuizResults)\
                .filter(Student.studentName == session["student"],\
                    QuizResults.student_id == Student.id,\
                    QuizResults.question_id == QuizMaster.id,\
                    QuizMaster.question == session["current_quiz"]["question"],\
                    QuizResults.course_id == course.id).all()

        if check:
            flash("Your Response for the previous question was already recorded. The quiz does not accept multiple submissions","completed")
        else:
            quiz_response = QuizResults()

            extract_student = db.session.query(Student).\
            filter(Student.studentName == session["student"]).all()[0]


            quiz_response.student_id = extract_student.id
            quiz_response.course_id = course.id
            quiz_response.created_dt = datetime.now(uae)

            extract_question = db.session.query(QuizMaster).\
            filter(QuizMaster.question == session["current_quiz"]["question"]).all()[0]

            quiz_response.question_id = extract_question.id

            if quiz_answer == session['current_quiz']['answer']:
                message =f"Correct!! {session['current_quiz']['explaination']}"
                flash(message,"correct")

                quiz_response.response = 1

            else:
                message =f"Wrong!! The Correct answer was {session['current_quiz']['answer']}. {session['current_quiz']['explaination']}"
                flash(message,"wrong")
                quiz_response.response = 0


            question_stats = db.session.query(QuizResults.question_id,\
            func.sum(QuizResults.response).label('correct'),\
            func.count(QuizResults.response).label('total'))\
                        .filter(QuizResults.question_id == QuizMaster.id,\
                        QuizMaster.question == session['current_quiz']['question'])\
                 .group_by(QuizResults.question_id).all()

            if question_stats:
                question_stats = question_stats[0]
                percentage = round((question_stats[1]/question_stats[2])*100,2)

            db.session.add(quiz_response)
            db.session.commit()

        # Proceed to Next Question

        # if question id number is less than total number of questions
        if session["current_quiz"]["id"] < session["total_quiz"]:
            # for the current course use the question id as the index, this will fetch the next question
            session["current_quiz"] = [game for game in session["quiz"][course.courseName]][session["current_quiz"]["id"]]
        else:
            return render_template("quiz/end_quiz.html",quiz_responses = quiz_responses,logo='/static/images/company_logo.png')

    else:
        session["current_quiz"] = [game for game in session["quiz"][course.courseName]][0]


    return render_template("quiz/start_quiz.html",quiz_responses = quiz_responses,
    check=check,logo='/static/images/company_logo.png',percentage=percentage)

@app.route('/quiz_process')
@login_required
def quiz_process():
    collection = [[s['question'] for s in q] for (theme,q) in quizapp.items()]
    questions = []
    counter = 0
    for q in collection:
        for question in q:
            search_question = db.session.query(QuizMaster).\
                filter(QuizMaster.question == question).all()
            if not search_question:
                counter += 1
                quiz_master = QuizMaster()
                quiz_master.question = question

                db.session.add(quiz_master)
                db.session.commit()

    return f"""{counter} questions added to master"""


@app.route('/activities',methods=['GET','POST'])
@login_required
def activity():

    activity = Activity.query.all()

    return render_template("activities.html", activity = activity,logo="/static/images/company_logo.png",title=page_title)


@app.route("/word_cookies_cheat",methods=["GET", "POST"])
def word_cookies_cheat():
    errors = ""
    result = ""
    letters = ""

    with app.open_resource('static/english_words.txt') as file:
        wordlist = [x.strip() for x in file.readlines()]

    if request.method == "POST":
        if request.form["letters"] is not None:
            letters = request.form["letters"]
            result = find_words(letters,wordlist)
        else:
            errors += f'Please Enter Letters'

    return render_template("word_cookies_cheat.html",solution=result, error_msg=errors)

@app.route("/moon_phase_calculator",methods=["GET", "POST"])
def moon_phase_calculator_func():
    errors = ""
    result = ""
    next_full = ""
    next_new = ""

    next_full = nextphasefm()
    next_new = nextphasenm()


    if request.method == "POST":
        selecteddate = request.form["date"]

        if selecteddate !='':
            result = specificdate(selecteddate)
        else:
            errors += f'Please select a Date'

    return render_template("moon_phase_calculator.html",moonphase=result,nextfull=next_full, nextnew = next_new, error_msg=errors)

@app.route("/typoglycemia",methods=["GET","POST"])
def can_still_read():
    errors = ""
    sentence = None
    result=''
    if request.method == "POST":
        if request.form["sentence"] is not None:
            try:
                sentence = request.form["sentence"]
                result = jumble(sentence)
            except:
                errors += f'Please type a sentence'
        else:
            errors += f'Please type a sentence'

    return render_template("typoglycemia.html",title="Can you read this?",s=result, error_msg=errors)

@app.route("/qr_code_generator",methods=["GET", "POST"])
def qr_code_app():


    if request.method == "POST":
        getURL = request.form["url"]
        print(getURL)
        #getURL = request.args.get("data", "")
        #return send_file(qrcode(getURL, mode="raw"), mimetype="image/png")
        return render_template("qr_code_generator.html",getURL=getURL)


    return render_template("qr_code_generator.html")


@app.template_filter()
def greeting(name):

    if datetime.now().hour >= 24:
        return f'Good Morning {name}'
    if datetime.now().hour >= 12:
        return f'Good Afternoon {name}'
    elif datetime.now().hour >= 16:
        return f'Good Evening {name}'

@app.template_filter()
def pluralize(number):
    if int(number) <= 1:
        return 'min.'
    else:
        return 'mins'

@app.route("/feedback",methods=['GET','POST'])
def feedback():
    if "student" not in session:
        print("Student not in session")
        return render_template("register.html")

    if request.method == "POST":
        feedback_dict = request.form
        feedback_list = []
        print(feedback_dict)
        for x in list(request.form):
            feedback_list.append(feedback_dict.getlist(x))

        print(feedback_list)

        # Update Student Table
        student = Student.query.filter_by(studentName = session["student"]).first()
        student.company = feedback_list[0][0]
        student.profession = feedback_list[1][0]

        db.session.commit()

        # Add Entry to Feedback Rating
        rating = FeedbackRating()
        rating.student_id = student.id
        rating.rating = int(feedback_list[2][0])
        rating.objective = int(feedback_list[5][0])
        rating.comments = feedback_list[6][0]

        db.session.add(rating)
        db.session.commit()

        # Add Entry to Likes
        for like in feedback_list[3]:
            likes = FeedbackFeatureOutcome()
            likes.student_id = student.id
            likes.feature_id = int(like)
            likes.outcome = 1

            db.session.add(likes)
            db.session.commit()

        # Add Entry to Likes
        for dislike in feedback_list[4]:
            dislikes = FeedbackFeatureOutcome()
            dislikes.student_id = student.id
            dislikes.feature_id = int(dislike)
            dislikes.outcome = 0

            db.session.add(dislikes)
            db.session.commit()

        flash("Thank you for your feedback","success")

        return redirect(url_for('feedback_results'))

    return render_template("feedback.html")

@app.route("/feedback_results",methods=['GET','POST'])
def feedback_results():

    ratings = db.session.query(FeedbackRating.rating,
        func.count(FeedbackRating.rating).label('rating'))\
        .group_by(FeedbackRating.rating).all()

    total_ratings = sum([r[1] for r in ratings])

    objs = db.session.query(FeedbackRating.objective,
        func.count(FeedbackRating.objective).label('objective'))\
        .group_by(FeedbackRating.objective).all()

    total_objs = sum([o[1] for o in objs])

    comments = db.session.query(FeedbackRating.comments)\
        .filter(func.char_length(FeedbackRating.comments)>=25)\
        .order_by(desc(FeedbackRating.id)).limit(10).all()


    likes = db.session.query(FeedbackFeatureOutcome.feature_id,FeedbackFeature.feature,\
        func.count(FeedbackFeatureOutcome.feature_id).label('feature'))\
        .filter(FeedbackFeatureOutcome.feature_id == FeedbackFeature.id,\
        FeedbackFeatureOutcome.outcome == 1)\
        .group_by(FeedbackFeatureOutcome.feature_id)\
        .order_by(desc(func.count(FeedbackFeatureOutcome.feature_id))).all()

    total_likes = sum([l[2] for l in likes])

    dislikes = db.session.query(FeedbackFeatureOutcome.feature_id,FeedbackFeature.feature,\
        func.count(FeedbackFeatureOutcome.feature_id).label('feature'))\
        .filter(FeedbackFeatureOutcome.feature_id == FeedbackFeature.id,\
        FeedbackFeatureOutcome.outcome == 0)\
        .group_by(FeedbackFeatureOutcome.feature_id)\
        .order_by(desc(func.count(FeedbackFeatureOutcome.feature_id))).all()

    total_dislikes = sum([l[2] for l in dislikes])

    return render_template("feedback_results.html",
    likes=likes,total_likes=total_likes,objs=objs,
    dislikes=dislikes,total_dislikes=total_dislikes,
    ratings=ratings,total_ratings=total_ratings,total_objs=total_objs,
    comments=comments)


@app.route('/apply_model',methods=['GET','POST'])
def apply_model():

    form = UploadForm()

    # buildmodel('/home/penrosedata/mysite/x_train.csv','/home/penrosedata/mysite/y_train.csv')

    if form.validate_on_submit():

        new_data = secure_filename(form.new_data.data.filename)

        form.new_data.data.save(new_data)

        df = predict_with_ml(new_data)

        return render_template('ml_predictions.html', tables=[df.to_html(classes='data')], titles=df.columns.values)

    return render_template('apply_model.html', form = form)
