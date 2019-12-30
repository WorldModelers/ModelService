import pandas as pd

def rainfall(row): 
    if row.counterfactual_class == 'Rainfall change':
        return row.counterfactual_level.split("%")[0]
    else:
        return 100
    
def irrigation(row): 
    if row.counterfactual_class == 'Irrigation':
        return int(row.counterfactual_level.split("=")[1].split("%")[0])
    elif row.counterfactual_class == 'Temperature change':
        if 'irrigated area=' in row.counterfactual_level:
            return int(row.counterfactual_level.split("irrigated area=")[1].split("%")[0])
        else: 
            return 0
    else:
        return 0    
    
def extension_package(row): 
    if row.counterfactual_class == 'Extension package':
        return int(row.counterfactual_level.split("%")[0])
    elif row.counterfactual_class == 'Temperature change':
        if 'additional uptake' in row.counterfactual_level:
            return int(row.counterfactual_level.split("%+")[1].split("%")[0])
        else: 
            return 0    
    else:
        return 0
    
def temperature(row): 
    if row.counterfactual_class == 'Temperature change':
        return float(row.counterfactual_level.split("+")[1].split("°")[0])
    else:
        return 0 
    
def pctl(pctl): 
    if pd.isna(pctl):
        return pctl
    else:
        return int(pctl.split("%")[0])

scenarios = pd.read_csv('Scenario_Parameters_Experiment_2020-01.csv')

scenarios['rainfall'] = scenarios.apply(lambda x: rainfall(x),axis=1)
scenarios['irrigation'] = scenarios.apply(lambda x: irrigation(x),axis=1)
scenarios['extension_package'] = scenarios.apply(lambda x: extension_package(x),axis=1)
scenarios['temperature'] = scenarios.apply(lambda x: temperature(x),axis=1)
scenarios['cereal_prodn_pctile'] = scenarios['cereal_prodn_pctile'].apply(lambda x: pctl(x))
scenarios['description'] = scenarios['simulation_mode']

scenarios = scenarios[['scenario',
                       'description',
                       'climate_anomalies',
                       'cereal_prodn_pctile',
                       'rainfall',
                       'irrigation',
                       'extension_package',
                       'temperature']]

scenarios.to_csv("Scenarios.csv", index=False)