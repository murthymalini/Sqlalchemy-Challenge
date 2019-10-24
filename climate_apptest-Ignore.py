# Imports

import numpy as np
import datetime as dt

from flask import Flask, jsonify

# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
import pandas as pd

# got lots of errors about using SQLAlchemy in multiple threads.
# I believe this is to protect database integrity if 
# multiple users are accessing your web page at same time.
# The 'check_same_thread' argument got rid of this, but would likely be a bad idea
# in a "real" application
engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread': False})

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# We can view all of the classes that automap found
Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

# sort date desc and grab first result
precip_results = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
last_date = dt.datetime.strptime(precip_results[0], "%Y-%m-%d")

# get start date by subtracting 1 from year.
# this could have issues during leap years, but I am ignoring that for now.
start_date = dt.datetime(last_date.year - 1, last_date.month, last_date.day).date()

# get most active station
# group by stations, count temperature observations per station, sort descending
station_count = session.query(Measurement.station, func.count(Measurement.tobs)).\
group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()

# most active station is first result from above
station_most_active = station_count[0][0]

# create a flask app
app = Flask(__name__)

# This function called `calc_temps` will accept start date and end date in the format '%Y-%m-%d' 
# and return the minimum, average, and maximum temperatures for that range of dates
def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    
    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

# create home page
@app.route("/")
def home():
    print("Server received request for 'Home' page...")
    return (
        "Welcome to the Honolulu weather measurements API!<br><br>"
        "/api/v1.0/precipitation<br>"
        "/api/v1.0/stations<br>"
        "/api/v1.0/tobs<br>"
        "/api/v1.0/&lt;start&gt;<br>"
        "/api/v1.0/&lt;start&gt;/&lt;end&gt;<br>"
    )

# return json of last year of precipitation data.
# I limired this to most active station to avoid warnings about
# dates appearing multiple times
@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for precipitation...")

    # Perform a query to retrieve the data and precipitation scores
    precip_results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.station == station_most_active).\
        filter(Measurement.date >= start_date).all()

    # place results in dataframe
    precip_df = pd.DataFrame(precip_results, columns = ["Date", "Precipitation"]).set_index("Date").dropna()

    # Sort the dataframe by date
    precip_df = precip_df.sort_values("Date")
    precip_dict = precip_df.T.to_dict()

    return jsonify(precip_dict)

# return json of all measurement stations
@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for stations...")

    station_results = session.query(Station.station, Station.name).all()

    station_df = pd.DataFrame(station_results, columns=["Station", "Name"]).set_index("Station")
    station_df = station_df.sort_values("Station")
    station_dict = station_df.T.to_dict()

    return jsonify(station_dict)

# return json of all temps for last year,
# again limited to most active station to avoid complaints
# about dates not being unique
@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for tobs...")

    # query temperature readings for last year, based on start date calculated earlier in notebook
    tobs_results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == station_most_active).\
        filter(Measurement.date >= start_date).all()

    # convert to a dataframe
    tobs_df = pd.DataFrame(tobs_results, columns=["Date", "Tobs"]).set_index("Date")
    tobs_df = tobs_df.sort_values("Date")
    tobs_dict = tobs_df.T.to_dict()

    return jsonify(tobs_dict)

# show aggregate temperature data from a user-defined start date in URL,
# by calling provided function with an end date of 9999-12-31.  May have to revisit
# this approach in ~8000 years.
@app.route("/api/v1.0/<start>")
def start_temps(start):

    temp_results = calc_temps(start, "9999-12-31")

    temp_df = pd.DataFrame(temp_results, columns=["TMin", "TAvg", "TMax"])
    temp_dict = temp_df.T.to_dict()

    return jsonify(temp_dict)

# show aggregate temperature data from a user-defined start date 
# and end date in URL, by calling provided function
@app.route("/api/v1.0/<start>/<end>")
def start_end_temps(start, end):

    temp_results = calc_temps(start, end)

    temp_df = pd.DataFrame(temp_results, columns=["TMin", "TAvg", "TMax"])
    temp_dict = temp_df.T.to_dict()

    return jsonify(temp_dict)

# run the flask page
if __name__ == "__main__":
    app.run(debug=True)