import os
import numpy as np
import pandas as pd
import pickle
from scipy import stats
from typing import Optional
from collections import defaultdict
from base.generation_module_gan import simulation
from base.questionnaries import empowerment_metric, calculate_p3ceq_score, health_literacy_evaluation, calculate_BSI, \
    calculate_eq_t5_categorical


def get_model(outcome: str, pilot) -> Optional[object]:
    model_path = f'base/Pilots/Models/{pilot}/{outcome}.pkl' if pilot else f'base/Models/{outcome}.pkl'
    if model_path and os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            return model
        except Exception as e:
            print(f"Error loading model from {model_path}: {e}")
            return None
    else:
        print(f"Model file does not exist: {model_path}")
        return None
def preprocess_simulated_people(simulated_df: pd.DataFrame) -> pd.DataFrame:
    """
    The model preprocess the simulated dataframe to apply intervention effect module
    :param simulated_df: simulated data DataFrame, rows are cancerless dataset questions and columns are simulated people
    :return: simulated dataframe with preprocessed indexes
    """
    bsi_columns = [63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80]
    eq_t0_cols = [83, 84, 85, 86, 87]
    health_literacy = [16, 17, 18]
    empowerment = [89, 99, 90, 100, 91, 101, 92, 102, 93, 103, 94, 104, 95, 105, 96, 106, 97, 107, 98, 108]  # 0..19

    P_centred_T0 = [124, 126, 128, 130, 132, 144, 146, 148]
    care_T0 = [134, 132, 144, 146]
    means_T0 = [136, 138, 140, 142]

    temporal_simulated = simulated_df.T
    temporal_simulated.columns = temporal_simulated.columns.astype(int)

    _, _, total_p3ceq = calculate_p3ceq_score(temporal_simulated, P_centred_T0, care_T0, means_T0)
    temporal_simulated['P3CEQ'] = total_p3ceq
    temporal_simulated = temporal_simulated.drop(set(P_centred_T0 + care_T0 + means_T0), axis=1)

    empowerment_t0 = empowerment_metric(temporal_simulated, empowerment)
    transformed_empowerment_t0 = {key: np.log1p(value) for key, value in empowerment_t0.items()}
    temporal_simulated['empowerment'] = transformed_empowerment_t0
    temporal_simulated = temporal_simulated.drop(empowerment, axis=1)

    temporal_simulated['health_literacy'] = health_literacy_evaluation(temporal_simulated, health_literacy)
    temporal_simulated = temporal_simulated.drop(health_literacy, axis=1)

    temporal_simulated['EQ_5D_5L'] = calculate_eq_t5_categorical(temporal_simulated, eq_t0_cols)
    temporal_simulated = temporal_simulated.drop(eq_t0_cols, axis=1)

    temporal_simulated['BSI'] = calculate_BSI(temporal_simulated, bsi_columns)
    temporal_simulated = temporal_simulated.drop(bsi_columns, axis=1)

    temporal_simulated.columns = temporal_simulated.columns.astype(str)
    return temporal_simulated.T


def result_statistic_analysis(p_value):
    if p_value < 0.05:
        return 'Statistically significant'
    else:
        return 'Non-statistically significant'

def increments(pos_t0, pos_t2, simulations, predictions):
    '''This method receives the outcomes to compute some general agregation data and returns the percentaje
    of improvement at t2 and if it is statiscally significant or not
    :param pos_t0: position outcome at T0
    :param pos_t2: position outcome in simulated data
    :param simulations: the entire simulation people
    :param predictions: the predicted value of each outcome
    :return: the percent of improvement and if it is statiscally significant or not
    '''
    if 'finish' not in (pos_t0, pos_t2):
        t0_outcome = list(simulations.loc[pos_t0, :])

        increment_outcome = predictions[pos_t2]

        t2_outcome = list()
        for person in range(0, len(increment_outcome)):
            t2_outcome.append(t0_outcome[person] + increment_outcome[person])

        count_of_improvement = 0
        for i in range(0, len(t2_outcome)):
            if t2_outcome[i] > t0_outcome[i]:
                count_of_improvement += 1

        percentaje_of_improvement = (count_of_improvement / len(t0_outcome)) * 100

        agregation = f'{np.round(np.mean(increment_outcome),2)} ({np.round(np.std(increment_outcome),2)})'

        statistical_analysis = stats.wilcoxon(t0_outcome, t2_outcome)

        return percentaje_of_improvement, agregation, statistical_analysis
    else:
        t2_finsh_intervention = predictions['finish']
        probabilities_finish = 0
        for i in range(0, len(t2_finsh_intervention)):
            if int(t2_finsh_intervention[i]) == 1:
                probabilities_finish += 1

        probability_finish = (probabilities_finish / len(t2_finsh_intervention)) * 100
        return probability_finish, None, None

def aggregation_module(simulations: pd.DataFrame, predictions: dict):

    health_part = defaultdict(list)
    social_part = defaultdict(list)
    adherence = defaultdict(list)
    rest_of_variables = defaultdict(list)

    link = {
        'Health_Rating': '88',
        'empowerment': 'empowerment',
        'Social_Worker_Visits': '176',
        'Emergency_Visits': '177',
        'finish': 'finish',

        'Personal_Quality': '81',
        'Specialist_Visits': '151',
        'Oncologist_Visits': '152',
        'Health_Satisfaction': '82',
        'Alcohol_Frequency': '30',
        'Psychoactive_Use': '32',
        'Sun_Exposure': '60',
        'Hospital_Stays': '178',
        'eq_5d_5l': 'EQ_5D_5L',
        'Primary_Care_Visits': '150',
    }

    oficial_names = {
        'Quality of life': ('Health_Rating', health_part),
        'Health Care Empowerment': ('empowerment', health_part),
        'Visits to Support Worker': ('Social_Worker_Visits', social_part),
        'Visits to emergency department': ('Emergency_Visits', social_part),
        'Adherence': ('finish', adherence),

        'Personal Quality': ('Personal_Quality', rest_of_variables),
        'Specialist Visits': ('Specialist_Visits', rest_of_variables),
        'Oncologist Visits': ('Oncologist_Visits', rest_of_variables),
        'Health Satisfaction': ('Health_Satisfaction', rest_of_variables),
        'Alcohol_Frequency': ('Alcohol_Frequency', rest_of_variables),
        'Psychoactive_Use': ('Psychoactive_Use', rest_of_variables),
        'Sun_Exposure': ('Sun_Exposure', rest_of_variables),
        'Hospital_Stays': ('Hospital_Stays', rest_of_variables),
        'EQ 5D 5L': ('eq_5d_5l', rest_of_variables),
        'Primary_Care_Visits': ('Primary_Care_Visits', rest_of_variables)

    }

    for display_name, (key, target_dict) in oficial_names.items():

        if predictions[key] is None:
            target_dict[display_name].append("-")
            target_dict[display_name].append("Not Avaliable")
            target_dict[display_name].append("-")
        else:
            increment, agregate, statistical = increments(link[key], key, simulations, predictions)
            target_dict[display_name].append(f'{round(increment, 2)}%')
            if display_name != 'Adherence':  # Adherence doesn't require statistical analysis
                target_dict[display_name].append(agregate)
                target_dict[display_name].append(result_statistic_analysis(statistical.pvalue))

    return health_part, social_part, adherence, rest_of_variables

def intervention_effect(steps: int, pilot: Optional[str] = None, ages: Optional[tuple] = None,
                        gender: Optional[int] = None, ethos: Optional[int] = None,
                        previous_homeless: Optional[int] = None, charlson: Optional[int] = None):

    question_path = os.getenv("QUESTION_PATH")
    questions_t0 = pd.read_csv(question_path, sep=';')

    simulations_ = simulation(steps, pilot, ages, gender, ethos, previous_homeless, charlson)

    if simulations_ is not None:
        outcomes = ['Health_Rating', 'Specialist_Visits', 'Oncologist_Visits', 'Personal_Quality',
                    'Health_Satisfaction', 'Alcohol_Frequency', 'Psychoactive_Use',
                    'Sun_Exposure', 'Social_Worker_Visits', "Emergency_Visits", "Hospital_Stays",
                    "Urgent_Hospital_Admissions", "Hospital_Nights",
                    'empowerment', 'eq_5d_5l', 'finish', 'smoke', 'Primary_Care_Visits']

        outcomes = [file.split('/')[-1].split('.')[0] for file in os.listdir('base/Models')]

        simulations = preprocess_simulated_people(simulations_)
        personal_predictions = defaultdict(list)
        for sim in simulations.columns.values:  # For all simulations
            for qn in outcomes:  # Take the model of the qn
                model = get_model(qn, pilot)  # get the correct model to predict or null if these model does not exist
                if model:
                    X_train = np.array(simulations[sim]).reshape(-1, 1)
                    prediction = model.predict(X_train.T)  # Prediction with my models
                    personal_predictions[qn].append(prediction[0])
                else:
                    personal_predictions[qn] = None
        health_part, social_part, adherence, rest_variables = aggregation_module(simulations, personal_predictions)

        return health_part, social_part, adherence, rest_variables
    else:
        return None
