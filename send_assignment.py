from sqlalchemy import update,create_engine,MetaData
import pandas as pd
import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#2.-Turn on database engine
project_dir = os.path.dirname(os.path.abspath(__file__))
dbEngine = create_engine("sqlite:///{}".format(os.path.join(project_dir, "client.db"))) # ensure this is the correct path for the sqlite file. 

sql_command = "SELECT s.id,c.id,c.courseName,s.studentName,s.email,cas.assignmentOrderNo,\
    ca.assignmentTitle,ca.assignmentDescription,ca.file_url,ca.file_url_solution \
    FROM course_assignment_subscription as cas \
    JOIN course as c \
    ON ca.courseId == c.id \
    JOIN course_assignment as ca \
    ON ca.courseId == cas.courseId \
    JOIN student as s \
    ON s.id == cas.studentId \
    WHERE cas.subscription == 1 \
    and cas.modified_dt <= DATE('now','-7 day')\
    and cas.assignmentOrderNo <= ca.assignmentOrder"

#3.- Read data with pandas
df = pd.read_sql(sql_command,dbEngine)

sender_email = "boardgameschedulers@gmail.com"
password = "pqozairzbntmvjpe"
message = MIMEMultipart("alternative")
message["From"] = 'Sunil Nair'

for index, row in df.iterrows():
    message["Subject"] = f"{row[2]} - Assignment {row[5]}"
    message["To"] = row[4]

    html = f'''
<p>Dear {row[3]},</p>
<span>Please find below instructions for your assignment.</span>
                    
<h3>{row[6]}</h3>
{row[7]}
'''
    if row[8]:
        html += f'''
<h4><a href='{row[8]}'>Download Exercise File</a></h4>
'''

    if row[9]:
            html += f'''
    <h4><a href='{row[9]}'>Download Solution for Assignment {row[5]-1}</a></h4>
    '''

    html += f'''
<span>Thank You</span><br/>
<span><b>Sunil Nair</b></span>
'''

    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, row[4], message.as_string()
        )

    meta = MetaData(bind=dbEngine)
    MetaData.reflect(meta)

    # Update the Course Assignment Subscription Table with the order Increment
    cas = meta.tables['course_assignment_subscription']

    u = update(cas)
    u = u.values({"assignmentOrderNo": row[5]+1})
    u = u.where(cas.c.courseId == row[1] and cas.c.studentId == row[0])
    
    # Insert into History Table
    ca_sent = meta.tables['course_assignment_sent']

    statement = ca_sent.insert().values(courseId=row[1], studentId=row[0],assignmentOrderNo=row[5])

    dbEngine.execute(u)
    dbEngine.execute(statement)
