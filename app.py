
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os 
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
load_dotenv()
app = Flask(__name__)
def get_db_connection():
    conn = psycopg2.connect(
        dbname='postgres',
        user='student',
        host='localhost',
        cursor_factory=RealDictCursor
    )
    return conn

   
@app.get("/")
def home():
    return "fuck the world"


##studen enpoits 
@app.route('/students', methods=['POST'])
def create_student():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students (name, email, phone, grade, race, birthday, gender, income, intended_major)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING student_id
    """, (data['name'], data['email'], data['phone'], data['grade'], data['race'], data['birthday'], data['gender'], data['income'], data['intended_major'],data['interest']))
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

def calculate_matching(student_interest, student_grade, student_intended_major, opprtunity_tags):
    score = 0 

    for tag in opprtunity_tags:
        if tag in student_interest:
            score += 2
        if tag in student_grade:
            score += 1
        if tag in student_intended_major:
            score += 3
    
    return score
@app.route('/recomender/<int:student_id>')
def createRecomendations(student_id):
    recstudent = students_df.loc[students_df.index == student_id].iloc[0]
        
    student_interest = recstudent['interest']
    student_grade = recstudent['grade']
    student_intended_major = recstudent['intended_major']
    
    match_scores = []
    for ind, row in opportunities_df.iterrows():
        opprtunity_tags = row['tags']
        match_score = calculate_matching(student_interest, student_grade,student_intended_major,opprtunity_tags)
        opportunities_df.at[ind, 'match_score'] = match_score
        match_scores.append({'opportunity': row['title'], 'match_score': match_score})
        
    print(match_scores) 
    return {'recommendations': match_scores}

if __name__ == "__main__":
    app.run(debug=True)

