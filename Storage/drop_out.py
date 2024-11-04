from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime
from sqlalchemy.sql.functions import now
from base import Base

class DropOut(Base):

    __tablename__ = "drop_out"

    id                      = Column(Integer, primary_key=True)
    student_id              = Column(String(250), nullable=False)
    program                 = Column(String(50), nullable=False)
    program_gpa             = Column(Numeric(4, 2), nullable=False)
    student_dropout_date    = Column(Date, nullable=False)
    date_created            = Column(DateTime, nullable=False)
    trace_id                = Column(String(250), nullable=False)

    def __init__(self, student_id, program, program_gpa, student_dropout_date, trace_id):
        self.student_id = student_id
        self.program = program
        self.program_gpa = program_gpa
        self.student_dropout_date = student_dropout_date
        self.date_created = now()
        self.trace_id = trace_id

    
    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "program": self.program,
            "program_gpa": self.program_gpa,
            "student_dropout_date": self.student_dropout_date,
            "date_created": self.date_created,
            "trace_id": self.trace_id
        }