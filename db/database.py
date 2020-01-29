from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import configparser

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')
print(config['DATABASE']['USER'])
engine = create_engine("postgresql://{0}:{1}@{2}:{3}/{4}"\
                        .format(config['DATABASE']['USER'],\
                                config['DATABASE']['PASSWORD'],\
                                config['DATABASE']['URL'],\
                                config['DATABASE']['PORT'],\
                                config['DATABASE']['DB'],),\
                        pool_recycle=3600,
                        )
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    Base.metadata.create_all(bind=engine)