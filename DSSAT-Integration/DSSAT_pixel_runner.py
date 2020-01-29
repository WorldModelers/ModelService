import os
import docker
import json

with open('et_docker.json','r') as f:
    config = json.loads(f.read())

base = os.getcwd()
output_dir = f"{base}{config.get('workDir').split('/userdata')[-1]}"
mgmt_practices = os.listdir(output_dir)

mgmt_dict = {}
for mgmt in mgmt_practices:
    upper = os.listdir(f"{output_dir}/{mgmt}")
    upper_dict = {}
    for u in upper:
        upper_dict[u] = os.listdir(f"{output_dir}/{mgmt}/{u}")
    mgmt_dict[mgmt] = upper_dict

pixel_dirs = []
for kk, vv in mgmt_dict.items():
        for yy, zz in vv.items():
            for z_ in zz:
                pixel_dirs.append(f"{output_dir}/{kk}/{yy}/{z_}")

if __name__ == "__main__":

    for d in pixel_dirs:
        print(d)
        snx = [i for i in os.listdir(d) if '.SNX' in i][0]
        os.chdir(d)
        os.system("docker run --rm --volumes-from ethdata -v ${PWD}:/data cvillalobosuf/dssat-csm A " + snx)