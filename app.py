
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os 
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
import bcrypt
load_dotenv()
app = Flask(__name__)
CORS(app)
def get_db_connection():
    conn = psycopg2.connect(
        dbname='postgres',
        user='student',
        host='localhost',
        cursor_factory=RealDictCursor
    )
    return conn



def get_students_df():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    df = pd.DataFrame(students)
    if not df.empty:
        df.set_index('student_id', inplace=True)
    return df
    
    
def get_opportunities_df():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM oppertunities')
    opportunites = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame(opportunites)


   
@app.get("/")
def home():
    return "fuck the world"



##studen enpoits 

## create new student/sign up 
@app.route('/students', methods=['POST'])
def create_student():
    data = request.json
    #password hasing
    password = data['password']
    bad_hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    password_hash = bad_hashed_password.decode('utf8') ## was having this problem https://stackoverflow.com/questions/34548846/flask-bcrypt-valueerror-invalid-salt idk why the comment i found the answer in used self. that doesnt make any sense to me but other than that the solution works fine
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT catagory FROM majors WHERE major = %s", (data['intended_major'],))
    major_catagory_result = cursor.fetchone()
    if major_catagory_result:
        major_catagory = major_catagory_result['catagory']
    else:
        return {'error': 'Invalid major'}, 400
    cursor.execute("""
        INSERT INTO students (name, email, phone, grade, race, birthday, gender, intended_major, interest, hashed_password)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING student_id
    """, (data['name'], data['email'], data['phone'], data['grade'], data['race'], data['birthday'], data['gender'], data['intended_major'],data['interest'], password_hash))
    student_id = cursor.fetchone()['student_id']
    conn.commit()
    cursor.close()
    conn.close()
    return ({'student_id': student_id}), 201

@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students where student_ID = %s',(student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    if student is None:
        return ({'error': 'Student not found'}), 404
    return (student),200

@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET name = %s, email = %s, phone = %s, grade = %s, race = %s, birthday = %s, gender = %s, income = %s, intended_major = %s
        WHERE student_id = %s
    """, (data['name'], data['email'], data['phone'], data['grade'], data['race'], data['birthday'], data['gender'], data['income'], data['intended_major'], student_id))
    conn.commit()
    cursor.close()
    conn.close()
    return '', 204
@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE student_ID = %s', (student_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return '', 204
@app.route('/students', methods=['GET'])
def list_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return (students)

## oppertunity endpoints
@app.route('/oppertunities/<int:oppertunity_id>', methods=['GET'])
def get_opportunity(oppertunity_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM oppertunities WHERE oppertunity_id = %s', (oppertunity_id,))
    opportunity = cursor.fetchone()
    cursor.close()
    conn.close()
    if opportunity is None:
        return ({'error': 'Opportunity not found'}), 404
    return (opportunity)

@app.route('/oppertunites',methods=['GET'])
def list_oppertunities():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM oppertunities')
    oppertunities = cursor.fetchall()
    cursor.close()
    conn.close()
    return (oppertunities)

##pandas dataframing
students_recfetch = list_students()
opportunities_recfetch = list_oppertunities()


students_df = pd.DataFrame(students_recfetch)
opportunities_df = pd.DataFrame(opportunities_recfetch)

students_df.set_index('student_id', inplace=True)
opportunities_df.set_index('oppertunity_id', inplace=True)
@app.route('/getdataframes')
def getstudentdfetch():
    print(students_df)
    print(opportunities_df['match_score'])
    return "pandas dataframe tester"

 #get dataframe info for a specific student   
@app.route('/getdataframes/<int:student_id>')
def df_findstudent(student_id):
    found_student = students_df.loc[students_df.index == student_id]
    print(found_student)
    return "finding student"


    
    
    ## recomendation system 
def df_findstudent(student_id):
    found_student = students_df.loc[students_df.index == student_id]
    print(found_student)
    return found_student

def calculate_matching(student_interest, student_grade, student_intended_major, opportunity_tags):
    ## validation check
    if not student_interest or not opportunity_tags:
        print("debug - student_interest:", student_interest)
        print("debug - opportunity_tags:", opportunity_tags)
        return 0
    score = 0 
    max_score_per_tag = 6
    max_possible_score = max_score_per_tag * len(opportunity_tags) if opportunity_tags else 1
    for tag in opportunity_tags:
        if tag in student_interest:
            score += 2
        if tag in student_grade:
            score += 1
        if tag in student_intended_major:
            score += 3
    factored_score = (score / max_score_per_tag) * 100
    return factored_score


@app.route('/recomender/<int:student_id>')
def createRecomendations(student_id):
    # Dynamically fetch the latest student data from the database
    students_df = get_students_df()
    print("Debug - student dataframe:", students_df.columns)
    opportunities_df = get_opportunities_df()
    print("Debug - opportunities dataframe:", opportunities_df.columns)

    # Ensure the student exists in the dataframe
    if student_id not in students_df.index:
        return {'error': 'Student not found'}, 404
    
    # Get the student's information
    recstudent = students_df.loc[students_df.index == student_id].iloc[0]
    print("Debug - student data:", recstudent)
        
    student_interest = recstudent['interest']
    student_grade = recstudent['grade']
    student_intended_major = recstudent['intended_major']

    print("student data:", recstudent)   
    
    recomendations = []
    for ind, row in opportunities_df.iterrows():
        opportunity_tags = row['tags']
        match_score = calculate_matching(student_interest, student_grade, student_intended_major, opportunity_tags)
        
        # Update the DataFrame with the match score
        opportunities_df.at[ind, 'match_score'] = match_score
        if match_score >= 80:
            recomendations.append({'opportunity': row['title'], 'match_score': match_score})
        
     
    print(student_interest)
    print(recomendations) 
    return {'recommendations': recomendations}



## fetch majors
@app.route('/majors',methods=['GET'])
def list_Majors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM majors')
    majors = cursor.fetchall()
    cursor.close()
    conn.close()
    return(majors)

## fetch interest 
@app.route('/interest',methods=['GET'])
def list_Interest():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM interestlist')
    interest = cursor.fetchall()
    cursor.close()
    conn.close()
    return(interest)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the student record based on the email
    cursor.execute('SELECT * FROM students WHERE email = %s', (email,))
    student = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if student is None:
        return {'error': 'Invalid email or password'}, 401
    
    # Verify the password
    if bcrypt.checkpw(password.encode('utf-8'), student['hashed_password'].encode('utf-8')):
        return {'message': 'Login successful', 'student_id': student['student_id']}, 200
    else:
        return {'error': 'Invalid email or password'}, 401

## for clawgame 
    ## pull random oppurtunity 

@app.route('/random_oppertunity', methods=['GET'])
def random_oppertunity():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM oppertunities ORDER BY RANDOM() LIMIT 1')
    random_oppertunity = cursor.fetchone()
    print("drawn oppertunity:",random_oppertunity)
    return(random_oppertunity)
    cursor.close()
    conn.close()
if __name__ == "__main__":
    app.run( debug=True)

