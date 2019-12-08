# from nostone.views import login_manager
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from geoalchemy2 import Geometry
from database import Base
import datetime
from hashlib import sha256

def hash_key(api_key):
    m = sha256()
    m.update(api_key.encode('utf-8'))
    return m.hexdigest()

# model, run_id,run_label,maas_model_version,raw_output_link?, point resolution,example_run, run_description
class Metadata(Base):
    __tablename__ = 'metadata'
    __table_args__ = {'extend_existing': True} 
    run_id = Column(String(120), unique=True, primary_key = True)
    run_label = Column(String(240), unique=False)
    model = Column(String(120), index=True)
    run_description = Column(String(1000), unique=False)
    model_version = Column(String(120), unique=False)
    point_resolution_meters = Column(Integer)
    raw_output_link = Column(String(1000), unique=False)

    def __repr__(self):
        return '<Metadata %r>' % (self.id)

class Output(Base):
    __tablename__ = 'output'
    __table_args__ = {'extend_existing': True} 
    id = Column(Integer, primary_key=True)
    run_id = Column(String(120), ForeignKey('metadata.run_id'), index=True)
    model = Column(String(120), index=True)
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)
    polygon = Column(String(1000), unique=False, index=True)
    datetime = Column(DateTime, index=True)
    feature_name = Column(String(120), unique=False, index=True)
    feature_value = Column(Float, index=True)
    feature_description = Column(String(240), unique=False)
    admin1 = Column(String(120), unique=False, index=True)
    admin2 = Column(String(120), unique=False, index=True)
    city = Column(String(120), unique=False, index=True)
    state = Column(String(120), unique=False, index=True)
    country = Column(String(120), unique=False, index=True)
    geom = Column(Geometry('POINT'), index=True)


    def __repr__(self):
        return '<Output %r>' % (self.id)

class Parameters(Base):
    __tablename__ = 'parameters'
    __table_args__ = {'extend_existing': True} 
    id = Column(Integer, primary_key=True)
    run_id = Column(String(120), ForeignKey('metadata.run_id'), index=True)
    model = Column(String(120), index=True)
    parameter_name = Column(String(240), unique=False, index=True)
    parameter_type  = Column(String(120), unique=False, index=True)
    parameter_value = Column(String(120), unique=False, index=True)


    def __repr__(self):
        return '<Parameters %r>' % (self.id)    