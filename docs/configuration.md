# Configuration

## Results Storage
You must ensure that the results stored by the model are readable and writable by the process running the server. This location is defined in `config.ini`. For example, for FSC in production this could look like:

```
[FSC]
OUTPUT_PATH = /home/ubuntu/ModelService/results/fsc/outputs
```

However you must ensure that this location is readable and writable by the process running the server. Results will be written by the model's Docker container (which may be `root`) so you likely need to `sudo chmod -r +777 /home/ubuntu/ModelService/results` or something like that to ensure appropriate permissions are set.


## NGINX Setup

You will need to configure NGINX to use the config called `model-service.conf` contained at the root of this project. You sould put the file at /etc/nginx/sites-available and symlink it to /etc/nginx/sites-enabled. To test the NGINX config use:

sudo nginx -t

If the config is acceptable then reload NGINX with:

sudo nginx -s reload

> Note: this assumes you've created the correct credentials with [CertBot](https://certbot.eff.org/).