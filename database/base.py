from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Association tables (must be defined here before they are referenced in model classes)

temporary_station_bands = Table(
    'temporary_station_bands',
    Base.metadata,
    Column('temporary_station_id', Integer, ForeignKey('temporary_stations.id'), primary_key=True),
    Column('band_id', Integer, ForeignKey('bands.id'), primary_key=True)
)

temporary_station_modes = Table(
    'temporary_station_modes',
    Base.metadata,
    Column('temporary_station_id', Integer, ForeignKey('temporary_stations.id'), primary_key=True),
    Column('mode_id', Integer, ForeignKey('modes.id'), primary_key=True)
)

event_bands = Table(
    'event_bands',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id'), primary_key=True),
    Column('band_id', Integer, ForeignKey('bands.id'), primary_key=True)
)

event_modes = Table(
    'event_modes',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id'), primary_key=True),
    Column('mode_id', Integer, ForeignKey('modes.id'), primary_key=True)
)
