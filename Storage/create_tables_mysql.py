import mysql.connector
from app import APP_CONFIG


db_conn = mysql.connector.connect(host=APP_CONFIG['datastore']['hostname'],
                                  user=APP_CONFIG['datastore']['user'], 
                                  password=APP_CONFIG['datastore']['password'], 
                                  database=APP_CONFIG['datastore']['db'])

db_cursor = db_conn.cursor()
db_cursor.execute('''
          CREATE TABLE enroll (
            id INT NOT NULL AUTO_INCREMENT,
            student_id VARCHAR(250) NOT NULL,
            program VARCHAR(50) NOT NULL,
            highschool_gpa DECIMAL(2,1) NOT NULL,
            student_acceptance_date DATE NOT NULL,
            program_starting_date DATE NOT NULL,
            date_created DATETIME NOT NULL,
            trace_id VARCHAR(250) NOT NULL,
            CONSTRAINT enroll_pk PRIMARY KEY (id)
          )
          ''')

db_cursor.execute('''
          CREATE TABLE drop_out (
            id INT NOT NULL AUTO_INCREMENT,
            student_id VARCHAR(250) NOT NULL,
            program VARCHAR(50) NOT NULL,
            program_gpa DECIMAL(2,1) NOT NULL,
            student_dropout_date DATE NOT NULL,
            date_created DATETIME NOT NULL,
            trace_id VARCHAR(250) NOT NULL,
            CONSTRAINT drop_out_pk PRIMARY KEY (id)
          )
          ''')

db_conn.commit()
db_conn.close()