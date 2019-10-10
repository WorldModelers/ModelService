# NGINX Setup

You will need to configure NGINX to use the config called `model-service.conf` contained at the root of this project. You sould put the file at /etc/nginx/sites-available and symlink it to /etc/nginx/sites-enabled. To test the NGINX config use:

sudo nginx -t

If the config is acceptable then reload NGINX with:

sudo nginx -s reload

> Note: this assumes you've created the correct credentials with [CertBot](https://certbot.eff.org/).