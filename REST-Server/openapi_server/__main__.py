#!/usr/bin/env python3

import connexion

from openapi_server import encoder

from flask_cors import CORS

def main():
    app = connexion.App(__name__, specification_dir='./openapi/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('openapi.yaml', 
    			validate_responses=True,
    			arguments={'title': 'ModelService API'})
    cors = CORS(app.app, supports_credentials=True)
    app.run(port=8080)


if __name__ == '__main__':
    main()