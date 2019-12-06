import oyaml as yaml
import glob
import pandas as pd

files = glob.glob('ontologies/UAZ-Ontologies/*tsv*')
model_paths = glob.glob('models/*model*yaml')

def remove_newline(description):
    '''
    Fixes trailing newline issue on yaml read/write
    '''
    if description[-1:] == '\n':
        return description[:-1]
    else:
        return description

def model_lookup(m, models, params, variables):
    '''
    Takes in a model metadata file and maps it to the various UAZ ontologies
    '''
    name = m['id'] 
    m['concepts'] = list(models[models['name']==name].sort_values('score', ascending=False)[:10]['concept'])
    m['description'] = remove_newline(m['description'])
    
    for p in m.get('parameters',[]):
        name = p['name']
        p['concepts'] = list(params[params['name']==name].sort_values('score', ascending=False)[:10]['concept'])
        p['description'] = remove_newline(p['description'])
    
    for o in m.get('outputs',[]):
        name = o['name']
        o['concepts'] = list(variables[variables['name']==name].sort_values('score', ascending=False)[:10]['concept'])        
        o['description'] = remove_newline(o['description'])
        
    return m            

# Generate dataframes for params, models, and variables
# This enables a lookup between a param, model or output variable name
# and the concept from the WM ontology.
# Note that only the top 10 (by rank) concepts are returned
for f in files:
    if 'parameter' in f:
        params = pd.read_csv(f, sep='\t', names=['type','concept','ontology','name','score'])
        params['name'] = params.name.apply(lambda x: x.split("MaaS-Parameters/")[1])
        params['concept'] = params.concept.apply(lambda x: x.split("/")[-1])
    if 'model' in f:
        models = pd.read_csv(f, sep='\t', names=['type','concept','ontology','name','score'])
        models['name'] = models.name.apply(lambda x: x.split("MaaS-Models/")[1])
        models['concept'] = models.concept.apply(lambda x: x.split("/")[-1])        
    if 'variable' in f:
        variables = pd.read_csv(f, sep='\t', names=['type','concept','ontology','name','score'])
        variables['name'] = variables.name.apply(lambda x: x.split("MaaS-Variables/")[1])
        variables['concept'] = variables.concept.apply(lambda x: x.split("/")[-1])        

# Write metadata files back to YAML
for model in model_paths:
    print(model)
    with open(model, 'r') as stream:
        m = yaml.safe_load(stream)
    stream.close()
        
    m = model_lookup(m, models, params, variables)
    ff = open(model, 'w+')
    yaml.dump(m, ff, allow_unicode=True)