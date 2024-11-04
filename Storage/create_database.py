import sqlite3

conn = sqlite3.connect("readings.sqlite")

c = conn.cursor()
c.execute('''
          CREATE TABLE enroll (
            id INTEGER PRIMARY KEY ASC,
            student_id VARCHAR(250) NOT NULL,
            program VARCHAR(50) NOT NULL,
            highschool_gpa DECIMAL(2,1) NOT NULL,
            student_acceptance_date DATE NOT NULL,
            program_starting_date DATE NOT NULL,
            trace_id VARCHAR(250) NOT NULL
          )
          ''')

c.execute('''
          CREATE TABLE drop_out (
            id INTEGER PRIMARY KEY ASC,
            student_id VARCHAR(250) NOT NULL,
            program VARCHAR(50) NOT NULL,
            program_gpa DECIMAL(2,1) NOT NULL,
            student_dropout_date DATE NOT NULL,
            trace_id VARCHAR(250) NOT NULL
          )
          ''')

conn.commit()
conn.close()