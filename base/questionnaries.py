from base.microsimulation_utilities import merge_questions, questionCategoriesT0, questionCategoriesT2
import numpy as np
import pandas as pd
from collections import Counter

"""
Calculate all questionnaires from CANCERLESS given certain parameters
"""
def qualy_eq_5d_5l(country: str, values: list) -> float:
    WEIGHTS = {
        # Spain - Book
        'Spain': {
            0: [0, 0.084, 0.099, 0.249, 0.337],
            1: [0, 0.050, 0.053, 0.164, 0.196],
            2: [0, 0.044, 0.049, 0.135, 0.153],
            3: [0, 0.078, 0.101, 0.245, 0.382],
            4: [0, 0.081, 0.128, 0.270, 0.348]
        },
        # important - The weights are for ENGLAND! (not UK)
        # Book
        'United Kingdom': {
            0: [0, 0.058, 0.076, 0.207, 0.274],
            1: [0, 0.050, 0.080, 0.164, 0.203],
            2: [0, 0.050, 0.063, 0.162, 0.184],
            3: [0, 0.063, 0.084, 0.276, 0.335],
            4: [0, 0.078, 0.104, 0.285, 0.289]
        },
        # Important - codes from Germany not from Greece
        # Paper: German Value Set for the EQ-5D-5L - Ludwig
        'Austria': {
            0: [0, 0.026, 0.042, 0.139, 0.224],
            1: [0, 0.050, 0.056, 0.169, 0.260],
            2: [0, 0.036, 0.049, 0.129, 0.209],
            3: [0, 0.057, 0.109, 0.404, 0.612],
            4: [0, 0.030, 0.082, 0.244, 0.365]
        }
    }

    """
    Only entrypoint for the EQ-5D-5L
    """
    # CHECKME - Depending on the study, it is compared with the English and the German sets
    # http://srv54.mednet.gr/archives/2001-2/180abs.html
    # https://onlinelibrary.wiley.com/doi/epdf/10.1111/j.1524-4733.2008.00356.x
    if country == 'Greece':
        country = 'United Kingdom'

    country_weights = WEIGHTS.get(country)
    # sanity check
    if not country_weights:
        return 0

    output = 1
    for i, val in enumerate(values):
        if pd.isnull(val):
            return np.nan
        output -= country_weights[i][int(val)]
    return output


def calculate_eq_t5(complete_df, questions):
    """
    complete_df = the dataframe to apply the EQ-5D-5L
    questions = the questions where the EQ-5D-5L is
    
    return = dicctionary with id user and his EQ-5D value.
    """
    pilots = sorted(list(set(complete_df.pilot)))
    t_values = dict()
    local_t_qol_col = list()

    for p in pilots:
        local_df = complete_df[complete_df.pilot == p]
        #for row in local_df.to_dict(orient='records'):
        for index,row in local_df.iterrows():
            values = []
            for col in questions:
                values.append(row[col])

            #t_values[row['id']] = qualy_eq_5d_5l(p, values)
            t_values[index] = qualy_eq_5d_5l(p, values)

    return t_values


def calculate_eq_t5_categorical(complete_df, questions):
    """
    complete_df = the dataframe to apply the EQ-5D-5L
    questions = the questions where the EQ-5D-5L is
    IN THIS VERSION PILOTS IS A CATEGORICAL ANSWER -> AUSTRIA = 0, GREECE = 1...
    return = dicctionary with id user and his EQ-5D value.

    """
    pilots=['Austria', 'Greece', 'Spain', 'United Kingdom']
    t_values = dict()
    local_t_qol_col = list()

    for p in range(0,len(pilots)):
        local_df = complete_df[complete_df[0] == p]
        # for row in local_df.to_dict(orient='records'):
        for index, row in local_df.iterrows():
            values = []
            for col in questions:
                values.append(row[col])

            # t_values[row['id']] = qualy_eq_5d_5l(p, values)
            t_values[index] = qualy_eq_5d_5l(pilots[p], values)

    return t_values

def calculate_BSI(complete_df, questions, delta=0):
    """
    CALCULATES BSI-18 Recklitis, C. J., Blackmon, J. E., & Chang, G. (2017). Validity of the brief symptom inventory-18 (BSI-18)
     for identifying depression and anxiety in young adult cancer survivors: Comparison with a structured
     clinical diagnostic interview. Psychological Assessment, 29(10), 1189–1200. https://doi.org/10.1037/pas0000427

        complete_df = the dataframe to apply the BSI
        questions = the questions where the BSI is
        delta = is the delta to make the questionnaire
        p = if true then calculate bsi by pilot if not for general
        return = dicctionary with id user and his BSI value.
    """

    local_t_qol_col = dict()
    if delta == 0:
        for i, row in complete_df.iterrows():
            total_sum = sum(row[question] for question in questions)
            local_t_qol_col[i] = total_sum

    else:
        for i, row in complete_df.iterrows():
            if sum(row[question] for question in questions) < delta:
                #local_t_qol_col[row['id']] = 1
                local_t_qol_col[i] = 1
            else:
                local_t_qol_col[i] = 2
    return local_t_qol_col


def calculate_qol(complete_df, column, question_df, T2=False):
    """
        complete_df = the dataframe to apply the categories of the quality of life
        column = the column to counter the number of appearances
        question_df = the dataframe for take the correct names
        T2 = checks if its for a T0 questionarie or T2
        return = a dicctionary with the categories and the number of appearances
    """

    res = {}

    question_categories = questionCategoriesT2(question_df, column) if T2 else questionCategoriesT0(question_df, column)

    complete_col = complete_df[column].fillna(-1)
    total = sum(Counter(complete_col).values())
    for k, v in Counter(complete_col).items():
        if k != -1:
            res[question_categories[int(k)]] = v
    return res

def health_literacy_evaluation(complete_df, columns):
    """
            complete_df = the dataframe to apply the categories of the quality of life
            columns = the columns to counter to calculate the health literacy

            return = a dicctionary with the id and the value of the health literacy
    """

    local_t_qol_col = dict()
    for i, row in complete_df.iterrows():
        local_t_qol_col[i] = sum(row[columns])
    return local_t_qol_col


def calculate_satisfaction(complete_df, column, question_df,T2=False):
    """
            complete_df = the dataframe to apply the categories of the quality of life
            column = the column to counter the number of appearances
            question_df = the dataframe for take the correct names
            T2 = checks if its for a T0 questionarie or T2
            return = a dicctionary with the categories and the number of appearances
        """

    satisfaction = dict()
    question_categories = questionCategoriesT2(question_df, column) if T2 else questionCategoriesT0(question_df, column)
    complete_col = complete_df[column]
    total = sum(Counter(complete_col).values())
    for k, v in Counter(complete_col).items():
        if k != -1:
            satisfaction[question_categories[int(k)]] = v
    return satisfaction

def calculate_p3ceq_score(complete_df, personal, care, means):
    """
    CALCULATES THIS p3ceq Lloyd, H., Fosh, B., Whalley, B., Byng, R., & Close, J. (2019).
    Validation of the person-centred coordinated care experience questionnaire (P3CEQ). International Journal for Quality in Health Care,
    31(7), 506–512. https://doi.org/10.1093/intqhc/mzy212

        complete_df = the dataframe to apply the BSI
        personal = the questions for p_centred
        care = the questions for care
        means = the questions for means

        return = dicctionary with id user and his pceq_total value.
        """
    pceq_total = dict()
    pcentred_personal = dict()
    care_personal = dict()

    for i, row in complete_df.iterrows():
        p_centred_score = sum(row[person] for person in personal) # Summartory of p_centred_score

        care_partial = row[care[0]]

        subquestion = np.mean(row[means[1:]]) if means[0] == 0 else 0
        care_total = sum(row[car] for car in care) + subquestion

        pcentred_personal[i] = p_centred_score

        care_personal[i] = care_total
        personal_p3ceq = p_centred_score + care_partial + subquestion

        pceq_total[i] = personal_p3ceq
    return pcentred_personal, care_personal, pceq_total

def empowerment_metric(complete_df, columns, T2=False):
    total_person = 0
    persons = dict()
    for index, row in complete_df.iterrows():
        all_columns = row[columns]
        if T2:
            for i in range(326, 345):
                combined = all_columns[i] * all_columns[i + 1]
                total_person += combined
            persons[index] = total_person
            total_person = 0
        else:
            for i in range(89, 99):
                combined = all_columns[i] * all_columns[i + 10]
                total_person += combined
            persons[index] = total_person if total_person > 0 else 0
            total_person = 0

    return persons