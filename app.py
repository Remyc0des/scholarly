from typing import Annotated
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Query, Depends
import os
from psycopg2.sql import SQL
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional
from enum import Enum
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
import bcrypt
from uuid import UUID
import random
import requests
import json
from sqlmodel import Field, Session, SQLModel, create_engine, select
from classes import GradeEnum, IncomeEnum, Swipe, gender, race, incone, StudentCreate, StudentPublic, StudentUpdate, Marker,OpportunitiesPublic, StudentRenty, Swipe
load_dotenv()

class Config:
    from_attributes = True # Allows Pydantic to read data from SQLAlchemy/Psycopg2 dicts


# old host adress = 192.168.1.81
def get_db_connection():
    database_url = "postgresql://neondb_owner:npg_HoEkftn6s1YF@ep-lucky-sun-ad0wuzh7-pooler.c-2.us-east-1.aws.neon.tech/ALEDUdb1?sslmode=require&channel_binding=require"
    result = urlparse(database_url)
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port = result.port,
        cursor_factory=RealDictCursor
    )
    return conn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Fuck The World"}




#**STUDENT ENDPOINTS**
###
###
###
# create new student/sign up
@app.post('/students', status_code=201)
async def create_student(student: StudentCreate):
    # password hasing
    password = student.password
    bad_hashed_password = bcrypt.hashpw(
        password.encode('utf-8'), bcrypt.gensalt())
    # was having this problem https://stackoverflow.com/questions/34548846/flask-bcrypt-valueerror-invalid-salt idk why the comment i found the answer in used self. that doesnt make any sense to me but other than that the solution works fine
    password_hash = bad_hashed_password.decode('utf8')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students (name, email, phone, grade, race, birthdate, gender, intended_major, income, gpa, hashed_password)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING student_id
    """, (student.name, student.email, student.phone, student.grade, student.race, student.birthdate, student.gender, student.intended_major, password_hash))

    new_id = cursor.fetchone()['student_id']
    conn.commit()
    cursor.close()
    conn.close()
    print(student)
    return {str(new_id)}

client = TestClient(app)

    


@app.get('/students/{student_id}', response_model=StudentPublic)
def get_student(student_id: UUID):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM students where student_ID = %s', (str(student_id),))
    student_data = cursor.fetchone()
    cursor.close()
    conn.close()
    #if student is None:
        # raise HTTPException(status_code=404, detail="Student not found")
    return student_data


@app.patch('/students/{student_id}')
async def update_student(student_id: UUID, student_data:StudentUpdate):
    ##Get dict of only the fields provided in request 
    update_data = student_data.model_dump(exclude_unset=True)
    #if statement returning error if not there
    if not update_data:
        raise HTTPException(status_code=400, detail="Issue Finding User Data")


    conn = get_db_connection()
    cursor = conn.cursor()

    #Build SET part of query dyanamically useing try except raise finally
    try:
        columns = update_data.keys()
        set_clause = ", ".join([f"{col} = %s" for col in columns])
        values = list(update_data.values())
        
        values.append(str(student_id))
    #Add student_id to end  of values list with same WHERE clause
        query = f"UPDATE students SET {set_clause} WHERE student_id = %s"
        cursor.execute(query, values)
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"message": "Update successful", "updated_fields": list(columns)}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        cursor.close()
        conn.close()
def seed_interests():
    # Replace with your actual Neon connection string
    
    try:
        conn = psycopg2.connect('postgresql://neondb_owner:npg_HoEkftn6s1YF@ep-lucky-sun-ad0wuzh7-pooler.c-2.us-east-1.aws.neon.tech/ALEDUdb1?sslmode=require&channel_binding=require', cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # 1. Fetch all Student UUIDs
        cur.execute("SELECT student_id FROM students")
        student_ids = [row['student_id'] for row in cur.fetchall()]

        # 2. Fetch all Marker IDs
        cur.execute("SELECT marker_id FROM markers")
        marker_ids = [row['marker_id'] for row in cur.fetchall()]

        if not student_ids or not marker_ids:
            print("Error: Ensure students and markers are seeded first!")
            return

        print(f"Linking {len(student_ids)} students to random interests...")

        # 3. Create the links
        for s_id in student_ids:
            # Pick 5 random unique interest IDs for each student
            chosen_markers = random.sample(marker_ids, 12)
            
            for m_id in chosen_markers:
                cur.execute("""
                    INSERT INTO student_interests (student_id, interest_id) 
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (s_id, m_id))
        
        conn.commit()
        print("Done! Every student now has more interests.")

    except Exception as e:
        print(f"Database error: {e}")


@app.delete('/students/{student_id}')
def delete_student(student_id:UUID):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE student_ID = %s', (str(student_id),))
    conn.commit()
    cursor.close()
    conn.close()
    return '', 204


@app.get('/students')
def list_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students')
    students = cursor.fetchall()
    seed_interests()
    cursor.close()
    conn.close()
    return (students)

# oppertunity endpoints


@app.get('/oppertunities/{oppertunity_id}',response_model=OpportunitiesPublic)
def get_opportunity(oppertunity_id:int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM opportunities WHERE opportunity_id = %s', (oppertunity_id,))
    opportunity = cursor.fetchone()
    cursor.close()
    conn.close()
    if opportunity is None:
        return ({'error': 'Opportunity not found'}), 404
    return (opportunity)


@app.get('/oppertunites')
def list_oppertunities():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM opportunities')
    oppertunities = cursor.fetchall()
    cursor.close()
    conn.close()
    return (oppertunities)


@app.get('/recomender/{student_id}')
def createRecomendations(student_id:UUID):
    conn = get_db_connection()
    cursor = conn.cursor()
    #algquery
    #cursor.execute("""           
    cursor.execute("""WITH swipe_similarity AS (SELECT o.opportunity_id AS current_opp_id, ss.swipe_type, 1 - (o.embedding <=> so.embedding) AS similarity FROM opportunities o  JOIN student_swipes ss ON ss.student_id = %s JOIN opportunities so ON so.opportunity_id = ss.opportunity_id WHERE 1 - (o.embedding <=> so.embedding) > 0.7) SELECT o.opportunity_id, o.title, SUM( CASE WHEN si.interest_id IS NOT NULL THEN 2 ELSE 0 END + CASE WHEN s.intended_major IS NOT NULL THEN 3 ELSE 0 END + CASE WHEN sw.swipe_type = 'saved' THEN 2 * sw.similarity ELSE 0 END + CASE WHEN sw.swipe_type = 'disliked' THEN -3 * sw.similarity ELSE 0 END ) AS raw_score, COUNT(ot.interest_id) AS tag_count, ( SUM( CASE WHEN si.interest_id IS NOT NULL THEN 2 ELSE 0 END + CASE WHEN s.intended_major IS NOT NULL THEN 3 ELSE 0 END ) * 100.0 / NULLIF(6 * COUNT(ot.interest_id), 0) ) AS normalized_score FROM opportunities o JOIN opportunity_tags ot ON o.opportunity_id = ot.opportunity_id LEFT JOIN student_interests si ON si.interest_id = ot.interest_id AND si.student_id = %s LEFT JOIN swipe_similarity sw ON sw.current_opp_id = o.opportunity_id JOIN students s ON s.student_id = %s GROUP BY o.opportunity_id, o.title;""",(str(student_id), str(student_id), str(student_id)) )
    
    #cursor.execute(algquery, str(student_id))
    cursor.fetchall()
    
# fetch majors
@app.get('/majors')
def list_Majors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM majors')
    majors = cursor.fetchall()
    cursor.close()
    conn.close()
    return (majors)



# fetch interest
@app.get('/markers')
async def list_markers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM markers')
    markers = cursor.fetchall()
    cursor.close()
    conn.close()
    return markers


@app.post('/login', response_model=StudentRenty)
def login():
    Student = StudentRenty
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the student record based on the email
    cursor.execute('SELECT * FROM students WHERE email = %s', (Student.email,))
    student = cursor.fetchone()

    cursor.close()
    conn.close()

    if student is None:
        return {'error': 'Invalid email or password'}, 401

    # Verify the password
    if bcrypt.checkpw(Student.password.encode('utf-8'), student['hashed_password'].encode('utf-8')):
        return {'message': 'Login successful', 'student_id': student['student_id']}, 200
    else:
        return {'error': 'Invalid email or password'}, 401

# for clawgame
    # pull random oppurtunity


##swipe saving route
@app.post('/student_swipe')
def handle_student_swipe(swipe:Swipe):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO student_swipes (student_id, opportunity_id, swipe_type)
        VALUES (%s, %s, %s)
        """, (swipe.student_id, swipe.oppertunity_id, swipe.swipe_type))
    conn.commit()
    cur.close()
    return ({'message': 'Swipe recorded'}), 200

@app.get('/saved_opportuniteies/{student_id}')
def get_saved_opportunities(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(""" 
        SELECT o.*
        FROM opportunities o
        JOIN student_swipes s ON s.opportunity_id = o.opportunity_id
        WHERE s.student_id = %s and s.swipe_type = 'saved'
    
    """, (student_id,))
    cur.close()
    conn.close()


@app.route('/random_oppertunity', methods=['GET'])
def random_oppertunity():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM opportunities ORDER BY RANDOM() LIMIT 1')
    random_oppertunity = cursor.fetchone()
    print("drawn oppertunity:", random_oppertunity)
    cursor.close()
    conn.close()
    return (random_oppertunity)


if __name__ == "__main__":
    app.run(debug=True)
