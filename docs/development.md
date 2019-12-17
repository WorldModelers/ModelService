# Development

MaaS is a Swagger application. To update an existing endpoint or to add a new one, you should update the `model_service_api.yaml` API specification file at the root of the project. 

To ensure that you have done this correctly, we recommend using the Swagger Editor.

### Swagger Editor
To use this, run the following:

```
docker pull swaggerapi/swagger-editor:latest
docker run -d -p 80:8080 swaggerapi/swagger-editor
```

This will run Swagger Editor (in detached mode) on port 80 on your machine, so you can open it by navigating to http://localhost in your browser.

### Open API Code Generation

Once you are satisfied with your API specification, you can generate stub code. Unfortunately, the current Swagger Editor does not support code gen for Open API 3.0 and Flask. To generate the server stub use:

```
wget http://central.maven.org/maven2/org/openapitools/openapi-generator-cli/3.3.4/openapi-generator-cli-3.3.4.jar -O openapi-generator-cli.jar

java -jar openapi-generator-cli.jar generate \
  -i model_service_api.yaml \
  -l python-flask \
  -o Rest-Server-UPDATE
```

This this will generate a new directory at the root of the project called `Rest-Server-UPDATE`. From here you should copy the new `openapi.yaml` file from this directory to `REST-Server/openapi/openapi/openapi.yaml`. You should be cautious about copying any other files but may wish to use the stub from the generated code to help add the endpoint to a controller.