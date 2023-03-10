import pandas as pd
# import numpy as np
# import joblib
import re
# from sklearn.ensemble import GradientBoostingClassifier
import pickle

def extract_number(years):
    search_term = '[0-9]'
    years_in_current_job = re.findall(search_term,years)
    return int("".join(years_in_current_job))


# def buildmodel(x,y):
#     x_train = pd.read_csv(x)
#     y_train = pd.read_csv(y)

#     selected_columns = list(x_train.columns)

#     gb = GradientBoostingClassifier(n_estimators=1000,random_state=100)
#     gb.fit(x_train, y_train)

#     with open("ml_model.pkl", "wb") as file:
#         pickle.dump(gb,file)
#         pickle.dump(list(x_train),file)


def predict_with_ml(new_data):

    original = pd.read_csv(new_data)
    df = original.copy()

    with open('/home/eibfsdata/mysite/ml_model.pkl','rb') as file:
        model = pickle.load(file)
        cols = pickle.load(file)

    df['Years in current job'] = df.apply(lambda x:extract_number(x['Years in current job']),axis=1)
    df['Term'].replace({'Short Term':1,'Long Term':2},inplace = True)
    df['Home Ownership'].replace({'HaveMortgage':'Home Mortgage'},inplace = True)
    cols_for_encoding = ['Home Ownership',
       'Purpose']

    for col in cols_for_encoding:
        new_df = pd.get_dummies(df[col], prefix=col)

        df = pd.concat([df,new_df],axis=1)
        df.drop(col,axis=1,inplace=True)

    # Load Model from Pickle

    df = df[cols][:]


    predict = model.predict(df)

    original.insert(0,"Prediction",predict)

    original["Prediction"].replace({0: "Non-Defaulter", 1: "Defaulter"},inplace=True)

    return original