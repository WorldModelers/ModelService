import os
import glob
import pandas as pd
from datetime import datetime

files = glob.glob('data/*.csv')

def parse_f(f):
    f = f.lower()
    if 'sensitivity' not in f:
        if 'maize' in f:
            out = {'crop': 'maize', 'temperature': 0, 'precipitation': 0, 'type': '2018 GLDAS Temperature/Precipitation'}
        elif 'wheat' in f:
            out = {'crop': 'spring wheat', 'temperature': 0, 'precipitation': 0, 'type': '2018 GLDAS Temperature/Precipitation'}
    else:
        if 'maize' in f:
            crop = 'maize'
        elif 'wheat' in f:
            crop = 'spring wheat'
        temp = f.split('sensitivitytest_t')[1].split('_')[0]
        precip = f.split('_')[-1].split('.csv')[0].split('w')[1]
        out = {'crop': crop, 'temperature': int(temp), 'precipitation': int(precip), 'type': 'Temperature/Precipitation Sensitivity Tests'}
    return out


if __name__ == "__main__":
    if not os.path.exists('data_processed'):
        os.mkdir('data_processed')

    df_ = pd.DataFrame()
    for f in files:
        df = pd.read_csv(f)
        params = parse_f(f)
        df['crop'] = params['crop']
        df['temperature'] = params['temperature']
        df['precipitation'] = params['precipitation']
        df['type'] = params['type']
        df['datetime'] = datetime(year=2018, month=1, day=1)
        df['% Yield Anomaly'] = df['% Yield Anomaly'].apply(lambda x: float(x))        
        
        f_out = f.split('data/')[1]
        df.to_csv(f"data_processed/{f_out}", index=False)
        
        df_ = df_.append(df)
        
    df_.to_csv('agmip.csv',index=False)