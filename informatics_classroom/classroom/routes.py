from flask import render_template,request, jsonify,session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField,FormField,FieldList
import numpy as np
import pandas as pd
from azure.cosmosdb.table.tableservice import TableService
from informatics_classroom.azure_func import init_cosmos
from informatics_classroom.classroom import classroom_bp
from informatics_classroom.classroom.forms import AnswerForm, ExerciseForm
from informatics_classroom.config import Keys

ClassGroups=sorted(['PMAP','CDA','FHIR','OHDSI'])


@classroom_bp.route('/home')
def landingpage():
    return render_template('home.html',title='Home')

@classroom_bp.route("/quiz",methods=['GET','POST'])
def quiz():
    return render_template('quiz.html')

@classroom_bp.route("/submit-answer",methods=['GET','POST'])
def submit_answer():
    if request.method=='GET':
        form=AnswerForm()
        return render_template('answerform.html',title='AnswerForm',form=form)
    sub_fields=['module', 'team', 'question_num', 'answer_num']
    for field in sub_fields:
        if field not in request.form.keys():
            return jsonify({"message":"Bad request, missing field {}".format(field)}),400
    # Get the answer key
    if 'class' in request.form.keys():
        #removing use of class as a variable name
        partition_key=request.form['class']
    else:
        partition_key=request.form['class_name']
    module_name=request.form['module']
    item_name=partition_key+"_"+ module_name
    container=init_cosmos('quiz','bids-class')
    output=container.read_item(item=item_name,partition_key=partition_key)
    questions=output['questions']
    question_num=int(request.form['question_num'])-1
    answer_num=request.form['answer_num']
    #Get the max RowKey and increment to make unique
    table_service = TableService(account_name=Keys.account_name, account_key=Keys.storage_key)
    RowKey=str(len(list(table_service.query_entities('attempts')))+1)

    attempt={'PartitionKey':item_name,
            'RowKey':RowKey,
            'course':partition_key,
            'module': module_name,
            'team': request.form['team'],
            'question': request.form['question_num'],
            'answer':str(answer_num)
    } 
          
    if str(questions[question_num]['correct_answer'])==str(answer_num):
        #Log success for team
        nextquestion=''
        attempt['correct']=1
        table_service.insert_or_replace_entity('attempts',attempt)
        return jsonify({"Message":"Great job! You got it right.","Next Question":nextquestion}),200
    else:
        #Log failure for team
        attempt['correct']=0
        table_service.insert_or_replace_entity('attempts',attempt)
        return jsonify({"message":"Sorry, wrong answer"}),406  
    return jsonify({"Something went wrong"}),400


@classroom_bp.route("/assignment/<exercise>")
def assignment(exercise):
    """Assignment home"""
    if not session.get("user"):
        #Test if user session is set
        session["return_to"]="classroom_bp.assignment"
        session['exercise']=exercise
        return redirect(url_for("auth_bp.login" ))
    if not session['user'].get('preferred_username').split('@')[1][:2]==Keys.auth_domain:
        #Test if authenticated user is coming from an authorized domain
        return redirect(url_for("auth_bp.login"))
    if len(exercise)==0:
        if 'return_to' in session.keys():
            exercise=session['exercise']
    user_name=session['user'].get('preferred_username').split('@')[0]
    container=init_cosmos('quiz','bids-class')
    #Query quizes in cosmosdb to get the structure for this assignment
    query = "SELECT * FROM c where c.id='{}'".format(exercise.lower())
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True )) 
    if len(items)==0:
        return "No assignment found with the name of {}".format(exercise)
    assignment=items[0]['questions']
    #Query Tableservice to get all attempts to answer questions for this assignment
    table_service = TableService(account_name=Keys.account_name, account_key=Keys.storage_key)
    tasks = table_service.query_entities('attempts', filter=f"team eq '{user_name}'") 
    df=pd.DataFrame(tasks)
    df=df[df['PartitionKey']=="{}".format(exercise.lower())]
    qnum,anum=0,0
    for i in range(0,len(assignment)):
        q_num=assignment[i]['question_num']
        attempts=len(df[df.question==str(q_num)])
        correct=len(df[(df.question==str(q_num))&(df.correct==1)])>0
        assignment[i]['attempts']=attempts
        assignment[i]['correct']=correct
        qnum+=1
        if correct==True:
            anum+=1
    df1=pd.DataFrame(assignment)
    df1.drop('correct_answer',axis=1, inplace=True)
    df1.sort_values('question_num',inplace=True)
    df1.reset_index(drop=True,inplace=True)
    return render_template("assignment.html",title='Assignment',user=session["user"],tables=[df1.to_html(classes='data',index=False)], exercise=exercise,qnum=qnum,anum=anum)

@classroom_bp.route("/exercise_review/<exercise>")
def exercise_review(exercise):
    """Exercise Review shows all the students and their progress on an Exercise"""
    if not session.get("user"):
        #Test if user session is set
        return redirect(url_for("auth_bp.login"))
    if not session['user'].get('preferred_username').split('@')[1][:2]==Keys.auth_domain:
        #Test if authenticated user is coming from an authorized domain
        return redirect(url_for("auth_bp.login"))
    
    #Test if user is an authorized user
    user_name=session['user'].get('preferred_username').split('@')[0]
    course_name=str(exercise).split('_')[0]   
    authorized_user=False
    container=init_cosmos('quiz','bids-class')
    items=container.read_item(item="auth_users",partition_key="auth")
    for name in items['users']:
        if user_name in name:
        # Test if user is in list of authorized users
            if course_name in name[user_name]:
                authorized_user=True
    if not authorized_user:
        return redirect(url_for("auth_bp.login"))      

    # Step 2 get the exercise Structure
    container=init_cosmos('quiz','bids-class')
    #Query quizes in cosmosdb to get the structure for this assignment
    query = "SELECT * FROM c where c.id='{}'".format(exercise.lower())
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True )) 
    if len(items)==0:
        return "No assignment found with the name of {}".format(exercise)
    assignment=items[0]['questions']
    # Step 3 get all the attempts made for that exercise
    table_service = TableService(account_name=Keys.account_name, account_key=Keys.storage_key)
    tasks = table_service.query_entities('attempts', filter=f"PartitionKey eq '{exercise}'") 
    df=pd.DataFrame(tasks)
    # Step 4 construct dataframe to send to html page
    df1=df.groupby(['team','question']).agg({'correct':np.max}).reset_index()
    df2=df1.pivot(index='team',columns='question').reset_index()
    df2['score']=df2.sum(axis=1)
    df1=df.groupby(['team','question'])['answer'].count().reset_index()
    df3=df1.pivot(index='team',columns='question').reset_index()
    return render_template("exercise_review.html",title='Exercise Review',user=session["user"],tables=[df2.to_html(classes='data',index=False),df3.to_html(classes='data',index=False)], exercise=exercise)

@classroom_bp.route("/exercise_form/<exercise>",methods=['GET','POST'])
def exercise_form(exercise):
    """Exercise Form"""
    #Step 1 get user information
    if not session.get("user"):
        #Test if user session is set
        return redirect(url_for("auth_bp.login"))
    if not session['user'].get('preferred_username').split('@')[1][:2]==Keys.auth_domain:
        #Test if authenticated user is coming from an authorized domain
        return redirect(url_for("auth_bp.login"))
    user_name=session['user'].get('preferred_username').split('@')[0]
    course_name=str(exercise).split('_')[0]
    # Step 2 get the exercise Structure
    container=init_cosmos('quiz','bids-class')
    #Query quizes in cosmosdb to get the structure for this assignment
    query = "SELECT * FROM c where c.id='{}'".format(exercise.lower())
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True )) 
    if len(items)==0:
        return "No assignment found with the name of {}".format(exercise)
    qnum=len(items[0]['questions'])
    #step 3 create form for that exercise
    class A(FlaskForm):
        a1 = StringField("Question Label")
    
    class B(FlaskForm):
        q=FieldList(FormField(A),min_entries=qnum)
        s=SubmitField("Submit Form")

    form=B()

    return render_template("exercise_form.html",form=form)

@classroom_bp.route("/studentcenter",methods=['GET','POST'])
def student_center():
    items=[]
    if not session.get("user"):
        return redirect(url_for("auth_bp.login"))
    if request.method=='POST':
        #Get course name
        class_name=request.form['wg1']
        #Get quiz format from Cosmos
        container=init_cosmos('quiz','bids-class')
        query = "SELECT * FROM c where c.class='{}' ORDER BY c.module".format(class_name.lower())
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True )) 
        #Get username
        user_name=session['user'].get('preferred_username').split('@')[0]
        #Get all attempts for that person
        table_service = TableService(account_name=Keys.account_name, account_key=Keys.storage_key)
        tasks = table_service.query_entities('attempts', filter=f"team eq '{user_name}'")
        df=pd.DataFrame(tasks)
        #filter for correct answers and course name
        df1=df[(df['correct']==1)&(df['course']==f"{class_name.lower()}")].copy()
        #Loop through all the question in the quiz and update any the user got correct
        for i in range(0,len(items)):
            for j in range(0,len(items[i]['questions'])):
                if len(df1[(df1.question==str(items[i]['questions'][j]['question_num']))&(df1.module==str(items[i]['module']))])>0:
                    items[i]['questions'][j]['correct']=True       
    return render_template("studentcenter.html",title='Student Center',form=ClassForm(),user=session["user"],items=items)

   

