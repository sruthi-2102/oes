from flask import Flask,redirect,render_template,url_for,request,jsonify,session,flash
from flask_mysqldb import MySQL
from datetime import date
from flask_session import Session
import mysql.connector 
from mysql.connector import OperationalError
from key import salt,salt2,secret_key
from otp import genotp
from sdmail import sendmail
from tokenreset import token
from stoken1 import token1
from itsdangerous import URLSafeTimedSerializer
app=Flask(__name__)
app.secret_key='#'
# app.config['MYSQL_HOST'] ='localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD']='root'
# app.config['MYSQL_DB']='exam'
mydb=mysql.connector.connect(host='localhost',user='root',password='jesuschrist@2004',db='exam')
app.config["SESSION_TYPE"] = "filesystem"
# mysql=MySQL(app)
Session(app)
@app.route('/')
def home():
    return render_template('homepage.html')
@app.route('/viewstudent')
def studentinfo():
    return render_template('studentclick.html')
@app.route('/viewadmin')
def admininfo():
    return render_template('adminclick.html')
@app.route('/studentsignin',methods=['GET','POST'])
def studentsignin():
    if request.method=='POST':
        firstname=request.form['firstname']
        lastname=request.form['lastname']
        mobilenumber=request.form['mobile']
        emailaddress=request.form['email']
        studentid=request.form['studentid']
        username=request.form['username']
        password=request.form['password']
        cpassword=request.form['cpassword']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from student where studentid=%s',[studentid])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from student where emailaddress=%s',[emailaddress])
        count1=cursor.fetchone()[0]
        if count == 1:
            flash('Studentid already existed')
            return redirect(url_for('studentsignin'))
        elif count1 == 1:
            flash('Email Address already existed')
            return redirect(url_for('studentsignin'))
        else:
            if password==cpassword:
                 otp = genotp()
                 var1={'firstname':firstname,'lastname':lastname,'contactnumber':mobilenumber,'emailaddress':emailaddress,'studentid':studentid,'username':username,'password':password,'fotp':otp}
                 subject = 'Registration OTP for STUDENT Account '
                 body=f"Thanks for signing up\n\nfollow this link for further steps-{otp}"
                 sendmail(to=emailaddress, subject=subject, body=body)
                 flash('OTP sent successfully')
                 return redirect(url_for('fotpform',fotp=token(data=var1, salt=salt)))
            else:
                    flash('Password not matched')
                    return redirect(url_for('studentsignin'))

                # cursor.execute('insert into student(firstname,lastname,contactnumber,emailaddress,studentid,username,password) values(%s,%s,%s,%s,%s,%s,%s)',[firstname,lastname,mobilenumber,emailaddress,studentid,username,password])
                # mydb.commit()
                # cursor.close()
                # return redirect(url_for('studentlogin'))
    return render_template('studentsignin.html')
@app.route('/fotpform/<fotp>',methods=['GET','POST'])
def fotpform(fotp):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        var1=serializer.loads(fotp,salt=salt)
    except Exception as e:
        flash('OTP expired')
        return render_template('otp.html')
    else:
        if request.method=='POST':
            otp=request.form['otp']
            if var1['fotp'] == otp :
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into student(firstname,lastname,contactnumber,emailaddress,studentid,username,password) values(%s,%s,%s,%s,%s,%s,%s)',[var1['firstname'],var1['lastname'],var1['contactnumber'],var1['emailaddress'],var1['studentid'],var1['username'],var1['password']])
                mydb.commit()
                cursor.close()
                flash('Registration Successfull')
                return redirect(url_for('studentlogin'))
            else:
                flash('Invalid OTP')
                return render_template('otp.html')
        return render_template('otp.html')
@app.route('/forgotf',methods=['GET','POST'])
def forgotf():
    if request.method=='POST':
        email=request.form['email']
        subject='RESET Link for password for STUDENT account'
        body=f"Click the link to verify the reset password:{url_for('verifyforgetf',data=token(data=email,salt=salt2),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Reset Link has been sent to your mail')
        return redirect(url_for('forgotf'))
    return render_template('forgot.html')
@app.route('/verifyforgetf/<data>',methods=['GET','POST'])
def verifyforgetf(data):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(data,salt=salt2,max_age=180)
    except Exception :
        flash('Link Expired')
        return redirect(url_for('forgotf'))
    else :
        if request.method=='POST':
            npassword=request.form['npassword']
            cpassword=request.form['cpassword']
            if npassword==cpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update student set password=%s where studentid=%s',[npassword,data])
                mydb.commit()
                flash("PASSWORD RESET SUCCESSFULLY")
                return redirect(url_for('studentlogin'))
            else:
                flash('PASSWORD NOT MATCHED')
                return redirect(url_for('verifyforgetf'))
    return render_template('newpassword.html')
@app.route('/ulogout')
def ulogout():
    if session.get('studentid'):
        session.pop('studentid')
        flash('Successfully logged out')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('studentlogin'))

##########################################
@app.route('/adminsignin',methods=['GET','POST'])
def adminsignin():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT count(*) from admin')
    result=int(cursor.fetchone()[0])
    cursor.close()
    if result>0:
        return render_template('noadmin.html')
    else:
        if request.method=='POST':
            firstname=request.form['firstname']
            lastname=request.form['lastname']
            mobilenumber=request.form['mobile']
            emailaddress=request.form['email']
            username=request.form['username']
            password=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into admin(firstname,lastname,mobilenumber,emailaddress,username,password) values(%s,%s,%s,%s,%s,%s)',[firstname,lastname,mobilenumber,emailaddress,username,password])
            mydb.commit()
            cursor.close()
            return redirect(url_for('adminlogin'))
    return render_template('adminsignin.html')
@app.route('/studentlogin',methods=['GET','POST'])
def studentlogin():
    if session.get('student'):
        return redirect(url_for('studentdashboard'))
    if request.method=='POST':
        studentid=request.form['studentid']
        user=request.form['user']
        password = request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from student where studentid=%s',[studentid])
        count=cursor.fetchone()[0]

        if count==1:
            cursor.execute('select password from student where studentid=%s',[studentid])
            confirm_password=cursor.fetchone()[0]
            cursor.execute('select username from student where studentid=%s',[studentid])
            user=cursor.fetchone()[0]
            if confirm_password==password:
                session['studentid']=studentid
                if not session.get(studentid):
                    session[studentid]={}
                return redirect(url_for("studentdashboard"))
            else:
                flash('Invalid password')
                return redirect(url_for('studentlogin'))
        else :
            flash('ACCOUNT NOT REGISTERED')
            return redirect(url_for('studentsignin'))
    return render_template('studentlogin.html')
@app.route('/studentbase')
def studentbase():
    user=session['user']
    return render_template('studentbase.html')
@app.route('/studentvalidate',methods=['POST'])
def studentvalidate():
    user=request.form['user']
    password=request.form['password']
    students=request.form['studentid']
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT studentid,username,password from student where studentid=%s',[students])
    data=cursor.fetchone()
    print(data)
    userid=data[1]
    print(userid)
    student_password=data[2]
    cursor.close()
    if user==userid and password==student_password:
        session['user']=user
        session['studentid']=students
        return redirect(url_for('studentbase'))
    else:
        return redirect(url_for('studentsignin'))
@app.route('/studentdashboard')
def studentdashboard():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT count(*) from courses')
    data=cursor.fetchone()[0]
    #total_courses=a[0]
    cursor.close()
    return render_template('studentdashboard.html',data=data)
@app.route('/coursedetails')
def studentcoursedetails():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT * from courses')
    courselist=cursor.fetchall()    
    cursor.close()
    return render_template('studentcoursedetails.html',courselist=courselist)
@app.route('/studentexam')
def studentexam():
    cursor=mydb.cursor(buffered=True)   
    cursor.execute('SELECT course_name from courses')
    data=cursor.fetchall()
    #data1=data[0]
    #print(data)
    #print(a)
    cursor.close()
    return render_template('studentexam.html',coursename=data)
@app.route('/examinstructions/<coursename>')
def takeexam(coursename):
    return render_template('takeexam.html',coursename=coursename)
@app.route('/attempts/<coursename>')
def attempt(coursename):
    students=session['studentid']
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select course_id from courses where course_name=%s',[coursename]);
    course_id=cursor.fetchone()[0]
    cursor.execute('select count(*) from submit where studentid=%s and course_id=%s',[students,course_id])
    result=int(cursor.fetchone()[0])
    if result>0:
        return render_template('noattempt.html')
    else:
        return redirect(url_for('takeexam',coursename=coursename))
@app.route('/submission')
def submit():
    return render_template('examsubmit.html')
@app.route('/startexam/<coursename>', methods=['GET', 'POST'])
def startexam(coursename):
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT course_id FROM courses WHERE course_name=%s', [coursename])
    course_id = cursor.fetchone()[0]
    cursor.execute('SELECT question_id, question, course_id, option1, option2, option3, option4, correctoption, marks FROM questions WHERE course_id=%s', [course_id])
    data = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        selected_option = request.form.get('options')
        student_id = session['studentid']

        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT question_id, correctoption, marks FROM questions WHERE course_id=%s', [course_id])
        questions_data = cursor.fetchall()
        cursor.close()

        total_marks = 0

        for question_data in questions_data:
            question_id = question_data[0]
            correct_option = question_data[1]
            marks = question_data[2]

            if selected_option == correct_option:
                total_marks += marks

            cursor = mydb.cursor(buffered=True)
            cursor.execute('INSERT INTO submit (optionselected, studentid, course_id, question_id, marks,total_marks) VALUES (%s, %s, %s, %s, %s,%s)', [selected_option, student_id, course_id, question_id, marks,total_marks])
            mydb.commit()
            cursor.close()

        # Redirect to a page displaying the total marks or any other relevant page
        return redirect(url_for('submit'))

    # Render the exam page
    return render_template('startexam.html', data=data)
@app.route('/studentmarks')
def studentmarks():
    students=session['studentid']
    #print(students)
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select distinct(course_id) from submit where studentid=%s',[students]);
    courseid=cursor.fetchall()
    #print(courseid)
    cursor.close()
    return render_template('studentmarks.html',courseid=courseid)  
@app.route('/astudentmarks')
def astudentmarks():
    #print(students)
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select distinct(course_id),studentid from submit')
    courseid=cursor.fetchall()
    #print(courseid)
    cursor.close()
    return render_template('astudentmarks.html',courseid=courseid)  
@app.route('/checkmarks/<courseid>',methods=['GET'])
def checkmarks(courseid):
    students=session['studentid']
    #print(students)
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select distinct(question_id) from submit where course_id=%s',[courseid])
    question_id=cursor.fetchall()
    cursor.execute('select count(question_id) from questions where course_id=%s',[courseid])
    data=cursor.fetchone()[0]
    cursor.execute('select sum(marks) from questions where course_id=%s',[courseid])
    data1=cursor.fetchone()[0]
    #print(question_id)
    cursor.execute('select optionselected from submit where studentid=%s and course_id=%s',[students,courseid])
    selectedoption=cursor.fetchall()
    #print(selectedoption)
    cursor.execute('select correctoption  from questions where course_id=%s',[courseid])
    correctoption=cursor.fetchall()
    print(correctoption)
    cursor.execute('select marks from questions where course_id=%s',[courseid])
    marks=cursor.fetchall()
    #print(correctoption)    
    for i in question_id:        
        count=0
        for l,m,n in zip(correctoption,selectedoption,marks):
            if l==m:
                count+=int(n[0])
            else:
                count+=0            
    cursor.close()
    return render_template('checkmarks.html',count=count,courseid=courseid,data=data,data1=data1)
@app.route('/acheckmarks/<courseid>',methods=['GET'])
def acheckmarks(courseid):
    
    #print(students)
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select distinct(question_id) from submit where course_id=%s',[courseid])
    question_id=cursor.fetchall()
    cursor.execute('select count(question_id) from questions where course_id=%s',[courseid])
    data=cursor.fetchone()[0]
    cursor.execute('select sum(marks) from questions where course_id=%s',[courseid])
    data1=cursor.fetchone()[0]
    #print(question_id)
    cursor.execute('select studentid from submit where course_id=%s',[courseid])
    count=cursor.fetchall()
    for j in count:
        print(j)
        cursor.execute('select optionselected from submit where studentid=%s and course_id=%s',[j[0],courseid])
        selectedoption=cursor.fetchall()
        #print(selectedoption)
        cursor.execute('select correctoption  from questions where course_id=%s',[courseid])
        correctoption=cursor.fetchall()
        print(correctoption)
        cursor.execute('select marks from questions where course_id=%s',[courseid])
        marks=cursor.fetchall()
        #print(correctoption)    
        for i in question_id:
            count=0
            for l,m,n in zip(correctoption,selectedoption,marks):
                if l==m:
                    count+=int(n[0])
                else:
                    count+=0            
    cursor.close()
    return render_template('acheckmarks.html',count=count,courseid=courseid,data=data,data1=data1,sid=j[0])
@app.route('/adminlogin')
def adminlogin():
    return render_template('adminlogin.html')
@app.route('/adminbase')
def adminbase():
    return render_template('adminbase.html')
@app.route('/adminvalidate',methods=['POST'])
def adminvalidate():
    user=request.form['username']
    password=request.form['password']
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT username,PASSWORD from admin ')
    data=cursor.fetchall()[0]
    userid=data[0]
    admin_password=data[1]
    cursor.close()
    if user==userid and password==admin_password:
        return redirect(url_for('adminbase'))
    else:
        return redirect(url_for('adminsignin'))
@app.route('/admindashboard')
def admindashboard():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT count(*) from student')
    data=cursor.fetchall()
    a=data[0]
    total_registered=a[0]
    cursor.execute('SELECT count(*) from courses')
    data1=cursor.fetchall()
    a=data1[0]
    total_courses=a[0]
    cursor.execute('SELECT count(*) from questions')
    data2=cursor.fetchall()
    a=data2[0]
    total_questions=a[0]
    cursor.close()
    return render_template('admindashboard.html',total_registered=total_registered,total_courses=total_courses,total_questions=total_questions)
@app.route('/adminstudent')
def adminstudent():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT count(*) from student')
    data=cursor.fetchall()
    a=data[0]
    total_registered=a[0]
    cursor.close()
    return render_template('adminstudent.html',total_registered=total_registered)
@app.route('/admincourse')
def admincourse():    
    return render_template('admincourse.html')
@app.route('/adminquestion')
def adminquestion():
    return render_template('adminquestion.html')
@app.route('/adminviewstudent')
def adminviewstudent():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT * from student')
    studentlist=cursor.fetchall()
    cursor.close()
    return render_template('adminviewstudent.html',studentlist=studentlist)
@app.route('/adminviewcourse')
def adminviewcourse():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT * from courses')
    courselist=cursor.fetchall()    
    cursor.close()
    return render_template('adminviewcourse.html',courselist=courselist)
@app.route('/cdelete/<cid>')
def cdelete(cid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('delete  from submit where course_id=%s',[cid])
    cursor.execute('delete  from courses where course_id=%s',[cid])
    mydb.commit() 
    cursor.close()
    return redirect(url_for('adminviewcourse'))
@app.route('/qdelete/<qid>')
def qdelete(qid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('delete  from submit where question_id=%s',[qid])
    cursor.execute('delete  from  questions where question_id=%s',[qid])
    mydb.commit() 
    cursor.close()
    return redirect(url_for('adminviewquestion'))
@app.route('/adminviewquestion')
def adminviewquestion():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT course_id,question,question_id from questions')
    questionslist=cursor.fetchall()
    cursor.close()
    return render_template('adminviewquestion.html',questionslist=questionslist)
@app.route('/adminaddcourse',methods=['GET','POST'])
def adminaddcourse():
    if request.method=='POST':
        courseid=request.form['courseid']
        coursename=request.form['coursename']
        duration=request.form['courseduration']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into courses(course_id,course_name,duration) values(%s,%s,%s)',[courseid,coursename,duration])
        mydb.commit()
        cursor.close()
        return redirect(url_for('adminviewcourse'))
    return render_template('adminaddcourse.html')
@app.route('/adminaddquestion',methods=['GET','POST'])
def adminaddquestion():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select course_id from courses')
    data=cursor.fetchall()
    cursor.close()
    if request.method=='POST':
        courseid=request.form['courseid']
        questionid=request.form['questionid']
        question=request.form['question']
        marks=request.form['marks']
        option1=request.form['option1']
        option2=request.form['option2']
        option3=request.form['option3']
        option4=request.form['option4']
        correctanswer=request.form['correctanswer']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into questions(question_id,question,course_id,option1,option2,option3,option4,correctoption,marks) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',[questionid,question,courseid,option1,option2,option3,option4,correctanswer,marks])
        mydb.commit()
        return redirect(url_for('adminquestion'))       
    return render_template('adminaddquestion.html',data=data)
# @app.route('/logout')
# def logout():
#     return render_template('logout.html')    
from collections import defaultdict

@app.route('/progress')
def progress():
    
    # Retrieve all submissions
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT studentid, course_id, question_id, total_marks FROM submit')
    submissions = cursor.fetchall()
    cursor.close()

    # Group submissions by student, course, and question
    progress_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for submission in submissions:
        student_id = submission[0]
        course_id = submission[1]
        question_id = submission[2]
        total_marks = submission[3]

        progress_data[student_id][course_id][question_id] = total_marks

    # Calculate progress percentage for each student, course, and question
    progress_percentage = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for student_id, courses in progress_data.items():
        for course_id, questions in courses.items():
            total_questions = len(questions)
            total_correct = sum(1 for marks in questions.values() if marks > 0)
            progress_percentage[student_id][course_id] = (total_correct / total_questions) * 100

    # Render the progress page with progress_percentage data
    return render_template('progress_page.html', progress=progress_percentage)

app.run(debug=True)
