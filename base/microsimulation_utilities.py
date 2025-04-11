from statistics import mode

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

def merge_questions(df: pd.DataFrame) -> pd.DataFrame:
    """
    The datasets downloaded in this version have different columns per translations
    the idea is to merge this columns
    """
    new_data = []
    # iterate over the dataframe as a list of dicts
    for row_ in df.to_dict('records'):
        new_row = {}
        for col, val in row_.items():
            # if the value is missing, ignore it
            if pd.isnull(val):
                continue
            # check if the column name starts with a number
            if col.strip()[0].isnumeric():
                question_number = int(col.split(')')[0].strip())
                new_row[question_number] = val
            # this is not a question, therefore just copy what was already there
            else:
                new_row[col] = val
        new_data.append(new_row)
    new_df = pd.DataFrame(new_data)
    nums = sorted([el for el in new_df.columns.values if isinstance(el, int)])
    sorted_headers = ['id', 'internal_code', 'pilot']+nums
    return new_df.reindex(sorted_headers, axis=1)

def columnsTypeT0(question_df:pd.DataFrame, question: int) -> str:
    return question_df.type.iloc[[question-1]][question-1]

def columnsNameT0(question_df:pd.DataFrame, question:int)-> str:
    return question_df.text.iloc[[question-1]][question-1]

def columnsTypeT2(questions_t2:pd.DataFrame, question: int) -> str:
    return questions_t2.type.iloc[[question-243]][question-243]

def columnsNameT2(question_df:pd.DataFrame, question:int)-> str:
    return question_df.text.iloc[[question-243]][question-243]

def questionCategoriesT0(question_df:pd.DataFrame, question:int)-> list:
    return [c.strip() for c in question_df.iloc[question - 1, :].categories.split('|')]

def questionCategoriesT2(question_df:pd.DataFrame, question:int)-> list:
    return [c.strip() for c in question_df.iloc[question - 243, :].categories.split('|')]

def change_values(old_pd: pd.DataFrame, question_df:pd.DataFrame,discarded:list) -> pd.DataFrame:
    """
    this method modifies the null values of the data set
    by their mean in the case of int or float values and
    by their mode in the case of categorical values.
    """
    new_df = old_pd.copy()
    columns = new_df.columns.values

    for column in columns[1:]:
        if column not in discarded:
            Tcolumna = columnsTypeT0(question_df, column)

            if new_df[column].isna().sum() == len(new_df[column]) and (Tcolumna == "categorical" or Tcolumna == "boolean"):
                value = -1
            elif new_df[column].isna().sum() == len(new_df[column]) and (Tcolumna in {"integer", "slider", "float"}):
                value = 0
            else:
                value = abs(mode(new_df[column].dropna())) if (
                            Tcolumna == "categorical" or Tcolumna == "boolean") else np.nanmean(new_df[column])

            for i,row in new_df.iterrows():
                if pd.isnull(row[column]) or ((Tcolumna == "categorical" or Tcolumna == "boolean") and (new_df.loc[i, column] == -1)):
                    new_df.loc[i, column] = round(value) if Tcolumna in {"integer", "slider"} else round(value, 2)
    return new_df

def preprocess_dataset(df: pd.DataFrame, questions):
    T0 = merge_questions(df)
    multiple_choice_questions = []
    discarded_questions = []

    for row in questions.itertuples():
        # Important - Only discarding text responses, multiple responses are admitted
        if row.type in {'text', 'longtext'}:
            discarded_questions.append(row.number)
        if row.type == 'multiple':
            multiple_choice_questions.append(row.number)

    # FILTERED T0 AND MODIFIED_T0
    filtered_t0 = T0.drop(discarded_questions + ['id','internal_code'], axis=1)

    return filtered_t0, multiple_choice_questions

def knn_train(X_train, y_train, X_test, y_test):
    clf = KNeighborsClassifier(n_neighbors=5)

    clf.fit(X_train, y_train)

    y_pred_train = clf.predict(X_train)
    y_pred_test = clf.predict(X_test)

    train_accuracy = accuracy_score(y_train, y_pred_train)
    test_accuracy = accuracy_score(y_test, y_pred_test)

    print("Train accuracy:", train_accuracy)
    print("Test accuracy:", test_accuracy)

    return clf

def rf_train(X_train, y_train, X_test, y_test):

    clf = RandomForestClassifier()

    clf.fit(X_train, y_train)

    y_pred_train = clf.predict(X_train)
    y_pred_test = clf.predict(X_test)

    train_accuracy = accuracy_score(y_train, y_pred_train)
    test_accuracy = accuracy_score(y_test, y_pred_test)

    print("Train accuracy:", train_accuracy)
    print("Test accuracy:", test_accuracy)

    return clf

def evaluate_model(y_true, y_pred, y_prob_test):

    accuracy = accuracy_score(y_true, y_pred)
    print("accuracy:", accuracy)

    precision = precision_score(y_true, y_pred, average='macro')
    print("precision (macro):", precision)

    recall = recall_score(y_true, y_pred, average='macro')
    print("Recall:", recall)

    f1 = f1_score(y_true, y_pred, average='macro')
    print("F1-score:", f1)

    custom = propensity_score(y_prob_test)
    print("Propensity Score:", custom)

def propensity_score(y_pred):
    sum = 0
    for pred in y_pred:
        aux = pred - 0.5
        sum += pow(aux, 2)

    score = sum / len(y_pred)
    return score

def evaluation_smote(original:pd.DataFrame,generated: pd.DataFrame):
    """this method recives a dataframe with the simulation people and aplies propensity score"""

    # class 0 for original dataset
    class_original = [0] * original.shape[0]

    original['class'] = class_original

    # class 1 for simulateds
    class_simulated = [1] * generated.shape[0]

    generated['class'] = class_simulated

    merged_data = pd.concat([original, generated], axis=0, ignore_index=True)

    X = merged_data.drop(['class'], axis=1)
    y = merged_data['class']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

    modelo = knn_train(X_train, y_train, X_test, y_test)
    y_pred_test = modelo.predict(X_test)
    y_prob_test = modelo.predict_proba(X_test)[:, 0]

    evaluate_model(y_test, y_pred_test, y_prob_test)

def evaluation(original:pd.DataFrame,generated: pd.DataFrame, method='knn'):
    """this method recives a dataframe with the simulation people and aplies propensity score"""

    merged_data = pd.concat([original, generated], axis=0, ignore_index=True)
    merged_data['class'] = [0 if i < 652 else 1 for i in range(0, merged_data.shape[0])]

    X = merged_data.drop(['class'], axis=1)
    y = merged_data['class']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    if method == 'knn':
        modelo = knn_train(X_train, y_train, X_test, y_test)
    else:
        modelo = rf_train(X_train, y_train, X_test, y_test)

    y_pred_test = modelo.predict(X_test)
    y_prob_test = modelo.predict_proba(X_test)[:, 0]

    evaluate_model(y_test, y_pred_test, y_prob_test)

def remove_columns(questions: pd.DataFrame) -> list:
    discarded_questions = []

    for row in questions.itertuples():
        # Important - Only discarding text responses, multiple responses are admitted
        if row.type in {'text', 'longtext'}:
            discarded_questions.append(row.number)
        if row.type == 'multiple' and row.number != 19:
            discarded_questions.append(row.number)

    return discarded_questions

def separate_dataset(df:pd.DataFrame, question_t0:pd.DataFrame):
    """Method to separate into categorical and numerical variables to handle different types of imputation"""
    categorical_features = list()
    categorical_features.append(0)
    numerical_features = list()
    for column in df.columns.values[1:]:
        if columnsTypeT0(question_t0,column) in {'categorical', 'boolean'}:
            categorical_features.append(column)
        else:
            numerical_features.append(column)
    return categorical_features, numerical_features