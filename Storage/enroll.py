from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric
from sqlalchemy.sql.functions import now
from base import Base
from datetime import datetime

class Enroll(Base):

    __tablename__ = "enroll"

    id                      = Column(Integer, primary_key=True)
    student_id              = Column(String(250), nullable=False)
    program                 = Column(String(50), nullable=False)
    highschool_gpa          = Column(Numeric(4, 2), nullable=False)
    student_acceptance_date = Column(Date, nullable=False)
    program_starting_date   = Column(Date, nullable=False)
    date_created            = Column(DateTime, nullable=False)
    trace_id                = Column(String(250), nullable=False)

    def __init__(self, student_id, program, highschool_gpa, student_acceptance_date, program_starting_date, trace_id):
        self.student_id = student_id
        self.program = program
        self.highschool_gpa = highschool_gpa
        self.student_acceptance_date = student_acceptance_date
        self.program_starting_date = program_starting_date
        self.date_created = now()
        self.trace_id = trace_id

    
    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "program": self.program,
            "highschool_gpa": self.highschool_gpa,
            "student_acceptance_date": self.student_acceptance_date,
            "program_starting_date": self.program_starting_date,
            "date_created": self.date_created,
            "trace_id": self.trace_id
        }