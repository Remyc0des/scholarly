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


class GradeEnum(str, Enum):
    freshman = "Freshman"
    sophomore = "Sophmore" 
    junior = "Junior"
    senior = "Senior"

class IncomeEnum(str, Enum):
    high = "High Income"
    low = "Low Income"
    middle = "Middle Income"
class gender(str, Enum):
    male = "Male"
    female = "Female"
    nonbinary = "Non-Binary"
class race(str, Enum):
    black = "Black"
    white = "White"
    asian =  "Asian"
    latin = "Latin/Hispanic"
class incone(str, Enum):
    hincome = "High Income"
    lincome = "Low Income"
    mincome = "Middle Income"

# 1. Used for POST /students
class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    grade: GradeEnum
    race: str
    birthdate: date
    gender: str
    intended_major: str
    password: str = Field(..., min_length=8) 

# 2. Used for GET /students
class StudentPublic(BaseModel):
    student_id: UUID
    name: str
    email: EmailStr
    grade: GradeEnum
    intended_major: str
    # Notice we EXCLUDE the hashed_password here for security
    
    class Config:
        from_attributes = True # Allows Pydantic to read data from SQLAlchemy/Psycopg2 dicts

# 3. Used for PUT /students (Profile updates)
class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    grade: Optional[GradeEnum] = None
    gpa: Optional[float] = None
    intended_major: Optional[str] = None


class Marker(BaseModel):
    marker_id: int
    name: str

class OpportunitiesPublic(BaseModel):
    opportunity_id: int
    title: str
    description: str
    opp_type: str
    institution: str
    eligibility: str
    deadline: datetime

class StudentRenty(BaseModel):
    email: str
    password: str



class swipetype(str, Enum):
    saved = "saved"
    disliked = "disliked"


class Swipe(BaseModel):
    student_id: UUID
    oppertunity_id: int
    swipe_type: swipetype




