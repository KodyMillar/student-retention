import mysql.connector

db_conn = mysql.connector.connect(host="172.26.186.84", user="kody",
password="ROMRAMRemRam!", database="events")

db_cursor = db_conn.cursor()

db_cursor.execute('''
                 DROP TABLE enroll, drop_out
                 ''')

db_conn.commit()
db_conn.close()