# Configuration

### Results Storage
You must ensure that the results stored by the model are readable and writable by the process running the server. This location is defined in `config.ini`. For example, for FSC in production this could look like:

```
[FSC]
OUTPUT_PATH = /home/ubuntu/ModelService/results/fsc/outputs
```

However you must ensure that this location is readable and writable by the process running the server. Results will be written by the model's Docker container (which may be `root`) so you likely need to `sudo chmod -r +777 /home/ubuntu/ModelService/results` or something like that to ensure appropriate permissions are set.
