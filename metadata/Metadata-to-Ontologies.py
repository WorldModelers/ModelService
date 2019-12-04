import yaml
import glob

def represent_none(self, _):
    return self.represent_scalar('tag:yaml.org,2002:null', '')

# Ensure that nulls are not dumped to yaml
yaml.add_representer(type(None), represent_none)

model_meta_files = glob.glob('models/*model*yaml')

models = [{'MaaS-Models':[]}]
variables = [{'MaaS-Variables': []}]
parameters = [{'MaaS-Parameters': []}]

for m in model_meta_files:
    with open(m, 'r') as stream:
        model = yaml.safe_load(stream)
        
    node = {'OntologyNode': None,
            'name': model['id'],
            'examples': [model['description'].replace('\n','')],
            'polarity': 1.0
           }

    models[0]['MaaS-Models'].append(node)   
    
    for var in model['outputs']:
        node = {'OntologyNode': None,
                'name': var['name'],
                'model': model['id'],                
                'examples': [var['description'].replace('\n','')],
                'polarity': 1.0
               }
        
        variables[0]['MaaS-Variables'].append(node) 
    
    if 'parameters' in model:
        for param in model['parameters']:
            node = {'OntologyNode': None,
                    'name': param['name'],
                    'model': model['id'],
                    'examples': [param['description'].replace('\n','')],
                    'polarity': 1.0
                   }

            parameters[0]['MaaS-Parameters'].append(node)         

ff = open('ontologies/MaaS-model-ontology.yaml', 'w+')
yaml.dump(models, ff, allow_unicode=True)

ff = open('ontologies/MaaS-variable-ontology.yaml', 'w+')
yaml.dump(variables, ff, allow_unicode=True)

ff = open('ontologies/MaaS-parameter-ontology.yaml', 'w+')
yaml.dump(parameters, ff, allow_unicode=True)