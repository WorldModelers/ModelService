import docker
import re

class KiController(object):
    """
    A controller to manage Kimetrica model execution.
    """

    def __init__(self):
        self.client = docker.from_env()
        self.scheduler = 'drp_scheduler:latest'
        self.db = 'drp_db:latest'
        self.entrypoint="python run.py --bucket=world-modelers --model_name=malnutrition_model --task_name=RasterToCSV --result_name=final/maln_raster_hires_baseline.csv --key=results/malnutrition_model/maln_raster_hires_baseline.csv"
        self.volumes = {'/home/ubuntu/darpa/': {'bind': '/usr/src/app/', 'mode': 'rw'}}
        self.environment = self.parse_env_file('darpa/kiluigi/.env')
        self.db_ports = {'5432/tcp': 5432}
        self.network_name = "kiluigi"
        self.environment['PYTHONPATH'] = '/usr/src/app:/usr/src/app/kiluigi'
        self.db_environment = {"APP": self.environment["APP"],
                          "ENV": self.environment["ENV"],
                          "PGPASSWORD": self.environment["PGPASSWORD"],
                          "POSTGRES_PASSWORD": self.environment["PGPASSWORD"]}
        self.network = self.create_network()
        self.db_container = run_db()


    def parse_env_file(self, path_to_file):
        """
        Parse a Kimetrica .env file into a dictionary
        Ultimately this should be deprecated in favor of
        a better approach to storing and loading environment variables
        and configurations for Kimetrica models executions.
        """
        envre = re.compile(r'''^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$''')
        env_var = re.compile(r'\$\{[0-9a-zA-Z_]*\}')
        alpha_num = re.compile(r'[0-9a-zA-Z_]+')
        result = {}
        with open(path_to_file) as ins:
            for line in ins:
                match = envre.match(line)
                if match is not None:
                    key = match.group(1)
                    val = match.group(2)
                    to_replace = env_var.findall(val)
                    for v in to_replace:
                        found = result[alpha_num.search(v).group(0)]
                        val = val.replace(v, found)
                    result[key] = val
        return result


    def create_network(self):
        """
        Establish network for communication between
        Kimetrica Docker containers.
        """
        for net in self.client.networks.list():
            if net.name == self.network_name:
                self.client.networks.get(net.id).remove()
        network = self.client.networks.create(self.network_name, driver="bridge")
        return network


    def run_db(self):
        """
        Run KiLuigi Database Docker container.
        """
        db_container = containers.run(self.db,
                                      environment=self.db_environment, 
                                      ports=self.db_ports, 
                                      network=self.network_name, 
                                      detach=True)    
        return db_container


    def run_model(self):
        """
        Run KiLuigi model inside Docker container
        """
        model = containers.run(self.scheduler, 
                               environment=self.environment, 
                               volumes=self.volumes, 
                               network=self.network_name, 
                               links={self.db_container.short_id: None},
                               entrypoint=self.entrypoint,
                               detach=True)
        return model


    def model_logs(self):
        """
        Return model logs
        """
        model_logs = model.logs()
        model_logs_decoded = model_logs.decode('utf-8')
        return model_logs_decoded