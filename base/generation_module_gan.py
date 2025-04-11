import ast
from typing import Optional
from ctgan import CTGAN
from base.microsimulation_utilities import merge_questions, remove_columns, separate_dataset
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer, SimpleImputer
import pandas as pd
import warnings
import os

warnings.filterwarnings('ignore')

def convert_to_list(s):
    if s == '[]':
        return []
    else:
        return ast.literal_eval(s)

def get_weight(value, charlson_index):
    """
    Look up the weight of a given value directly from the charlson_index dictionary.
    """
    for weight, indices in charlson_index.items():
        if value in indices:
            return weight  # Key is weight
    return 0

def pre_process(df_t0, questions_t0, pilot=None):
    T0 = merge_questions(df_t0)
    filtered_t0 = T0.drop(['internal_code', 'id'], axis=1)

    # modify pilot from STRING to CATEGORICAL
    filtered_t0['pilot'] = filtered_t0['pilot'].astype('category')
    filtered_t0['pilot'] = filtered_t0['pilot'].cat.codes
    filtered_t0.rename(columns={'pilot': 0}, inplace=True)

    if pilot is not None:
        filtered_t0 = filtered_t0[filtered_t0[0] == pilot]

    charlson_index = {
        1: [0, 1, 2, 3, 10, 4, 5, 6, 7, 8],
        2: [16, 9, 12, 11],
        3: [13],
        4: [14, 15]
    }
    # PREPROCESS COLUMN 19 to charlson comorbidity
    total_sum = 0

    filtered_t0[19] = filtered_t0[19].apply(convert_to_list)

    for person,row in filtered_t0.iterrows():
        if len(row[19]) > 0:
            for value_ in row[19]:
                value = int(value_)
                weight = get_weight(value, charlson_index)
                total_sum += weight
        else:
            total_sum = 0
        filtered_t0.loc[person, 19] = total_sum
        total_sum = 0

    if pilot is not None:
        if pilot == 0:
            drop_columns = [8, 13, 29, 35, 37, 62, 125, 127, 129, 131, 133, 135, 137, 139, 141, 143, 145, 147, 149, 156, 157, 159, 160, 165,
         166, 168, 169, 171, 172, 174]
        elif pilot == 1:
            drop_columns = [12, 29, 35, 37, 125, 127, 133, 135, 137, 139, 141, 143, 145, 147, 149, 156, 157, 159, 160, 165, 168, 169, 171, 172]
        elif pilot == 2:
            drop_columns = [22, 29, 35, 37, 45, 46, 62, 125, 127, 129, 131, 133, 135, 137, 139, 141, 143, 145, 147, 149, 150, 151, 152, 153,
                            154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180]
        else:
            drop_columns = [12, 37, 156, 157, 165, 166, 168, 169, 171, 172]
    else:
        drop_columns = [ 8, 12, 22, 24, 25, 26, 29, 35, 37, 45, 46, 62, 125, 127, 129, 131, 133, 135,
                         137, 139, 141, 143, 145, 147, 149, 154, 156, 157, 159, 160, 162, 163, 165, 166,
                         168, 169, 171, 172, 174, 175
        ]

    discardeds = remove_columns(questions_t0) + drop_columns

    originals = filtered_t0.drop(discardeds, axis=1)

    # imputation for rest variables
    cat_features, num_features = separate_dataset(originals, questions_t0)
    categorical_df = originals[cat_features]
    numerical_df = originals[num_features]
    iter_imputer = IterativeImputer(random_state=0)
    imputed_num = pd.DataFrame(iter_imputer.fit_transform(numerical_df), columns=numerical_df.columns.values)
    simple_imputer = SimpleImputer(strategy='most_frequent')
    imputed_cat = pd.DataFrame(simple_imputer.fit_transform(categorical_df), columns=categorical_df.columns.values)

    final_t0 = pd.concat([imputed_num, imputed_cat], axis=1).sort_index(axis=1)

    # for ctgan
    categoricals = list()
    categoricals.append(0)
    integers = list()

    for id, row in questions_t0.iterrows():
        if row.number not in discardeds and row.group != 'Satisfaction':
            if row.type in ['slider', 'float', 'integer']:
                integers.append(row.number)
            else:
                categoricals.append(row.number)
    final_t0[categoricals] = final_t0[categoricals].astype(int)


    final_t0[integers] = final_t0[integers].astype(float)

    final_t0.columns = [str(qn) for qn in final_t0.columns.values]
    discrete_columns = [str(qn) for qn in categoricals]

    return final_t0, discrete_columns
def simulate_one_case(original_distribution_df: pd.DataFrame, discrete_columns: list, data_sample :int = 652) -> dict:

    #Define our CTGAN epochs
    ctgan = CTGAN(epochs=100)
    ctgan.fit(original_distribution_df, discrete_columns)

    # Create synthetic data
    synthetic_data = ctgan.sample(data_sample)
    return dict(synthetic_data)
def generate_simulations(original_distribution_df: pd.DataFrame, cat_features: list, target_individuals: int,
                         parameters: dict) -> Optional[list]:
    """
    Generate a population by invoking the 'simulate_one_case' and apply filters to ensure the population meet
    the parameters specified for the simulation

    :param original_distribution_df: Original data to sample from
    :param target_individuals: Number of individuals in the population to generate
    :param parameters: A dictionary {question_number:value} to filter the simulations
    :param stop_attempts: Percentage of the target individual accepted as failed simulation attempts (e.g.,
    when target_individuals=100 and stop_attempts=2 the algorithm will allow for 200 failed simulations)
    :return: filtered simulation
    """
    population = []
    attempts = 0

    simulations = simulate_one_case(original_distribution_df, cat_features)

    while len(population) < target_individuals and attempts < len(simulations['1']):

        for question, value in parameters.items():
            qn = str(question)

            # The parameter doesn't have a value. But it will be better to not include it :3
            if value is None:
                continue
            # Age case - This could be generic checking for type of value, if tuple it is a range
            if qn == '1':
                # Assuming value here is a tuple
                if not (value[0] <= simulations[qn][attempts] <= value[1]):  # sim[qn]
                    attempts += 1
                    break
            elif qn == 'bsi':
                d_t0_cols = [63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80]
                personal = 0
                for question in d_t0_cols:
                    personal += simulations[question][attempts]
                if personal != value:
                    attempts += 1
                    break
            # Any other case
            else:
                if simulations[qn][attempts] != value:
                    attempts += 1
                    break

        # For else execute if the loop has completed normally (didn't reach a break)
        else:
            aux_dict = dict()
            for clave, valores in simulations.items():
                if attempts < len(valores):
                    aux_dict[clave] = simulations[clave][attempts]
            population.append(aux_dict)
            attempts += 1

    return population

def simulation(steps, pilot:int=None, ages:tuple=None, gender:int=None, ethos:int=None, homeless:int=None, charlson:int=None, bsi:int=None)->Optional [pd.DataFrame]:
    """
        Generate a population by invoking the 'simulate_one_case' and apply filters to ensure the population meet
        the parameters specified for the simulation
        Main method for generate people, this method receives the parameters and extract final result in a dataframe
        :param steps: how many people to generate
        :param pilot: which pilot comes from
        :param ages: ages of the people to simulate
        :param gender: gender of the people to simulate
        :param ethos: ethos category of people
        :param homeless: simulate people that have experienced homeless before or not
        :param charlson: charlson comorbidity people
        :param bsi: BSI index of people
        :return:
        """
    question_path = os.getenv("QUESTION_PATH")
    dataset_path = os.getenv("DATASET_PATH")

    t0_path = f'base/export_T0_All.csv'
    df_t0 = pd.read_csv(dataset_path, sep=';')
    questions_t0 = pd.read_csv(question_path, sep=';')

    categorical_pilot = {'Austria': 0, 'Greece': 1, 'Spain': 2, 'United Kingdom': 3}
    print("pilot",categorical_pilot[pilot] if pilot is not None else None)
    preprocessed_t0, discrete_columns = pre_process(df_t0, questions_t0, categorical_pilot[pilot] if pilot is not None else None)

    # parametization variables
    print("Population", steps)
    print("Range of ages", ages)
    print("Gender", gender)
    print("Previous homeless", homeless)
    print("ETHOS", ethos)
    print("Charlson comorbidity index", charlson)
    print("BSI", bsi)

    parameters = dict()
    parameters[1] = ages
    parameters[2] = gender
    parameters[7] = homeless
    parameters[9] = ethos
    parameters[19] = charlson
    parameters['bsi'] = bsi

    microsimulations_ = []
    generateds_cases = 0

    fails = steps * 2
    while generateds_cases < steps and fails > 0:
        microsimulations_aux = generate_simulations(preprocessed_t0, discrete_columns, steps - generateds_cases, parameters)

        if len(microsimulations_aux) == 0:
            fails -= 1
        else:
            microsimulations_.extend(microsimulations_aux)
            generateds_cases += len(microsimulations_aux)

    print("Finished generating")

    if len(microsimulations_) > 0:
        microsimulations = pd.DataFrame(microsimulations_)
        microsimulations = microsimulations.T
        return microsimulations
    else:
        return None