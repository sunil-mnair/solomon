import sqlalchemy
import pandas as pd
import os
import json

#2.-Turn on database engine
project_dir = os.path.dirname(os.path.abspath(__file__))
dbEngine=sqlalchemy.create_engine("sqlite:///{}".format(os.path.join(project_dir, "client.db"))) # ensure this is the correct path for the sqlite file. 

#3.- Read data with pandas
df1 = pd.read_sql('select * from quiz_master',dbEngine)
#df2 = pd.read_csv('questions.csv',engine='python',encoding_errors='ignore')

df3 = pd.read_sql('select * from quiz_results',dbEngine)
#df4 = pd.read_csv('quiz_questions.csv')


quiz_responses = pd.merge(df3, 
                      df1, 
                      on ='question', 
                      how ='inner')



# student_master_responses.rename(columns={ student_master_responses.columns[5]: "student_id" },inplace=True)
# student_master_responses.rename(columns={ student_master_responses.columns[4]: "course_id" },inplace=True)


# course_question_master = pd.merge(df4, 
#                       df3, 
#                       on ='courseName', 
#                       how ='inner')

# course_question_master.rename(columns={ course_question_master.columns[2]: "course_id" },inplace=True)

#inner_join.rename({'id':'course_id'},inplace=True)



#4.- I also want to add a new table from a dataframe in sqlite (a small one) 
#df2.to_sql(name = 'quiz_master',con= dbEngine, index=False, if_exists='append') 


# final_responses = pd.merge(student_master_responses, 
#                       course_question_master, 
#                       on ='question', 
#                       how ='inner')

#final_responses.to_csv("responses_for_upload.csv")

#df_todb = pd.read_csv('responses_for_upload.csv')
#df_todb.to_sql(name = 'quiz_results',con= dbEngine, index=False, if_exists='append') 

quiz_responses = quiz_responses.iloc[:,0:9]


quiz_responses.rename(columns={ quiz_responses.columns[0]: "id",quiz_responses.columns[5]: "created_dt",quiz_responses.columns[6]: "modified_dt",quiz_responses.columns[7]: "delete_id",quiz_responses.columns[8]: "question_id" },inplace=True)


quiz_responses.drop(['delete_id'], axis=1)
print(quiz_responses.columns)

quiz_responses.to_sql(name = 'quiz_results',con= dbEngine, index=False, if_exists='replace') 