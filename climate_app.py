
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
from sqlalchemy import distinct
from flask import Flask, jsonify


engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread': False})
Base = automap_base()
Base.prepare(engine, reflect=True)




Measurement = Base.classes.measurement
Station = Base.classes.station
session = Session(engine)
connection = engine.connect()


app = Flask(__name__)


@app.route('/')
def welcome():
    return(
    f"<h1>The following are links to APIs:</h1><br><br>"
    f"<a href='/api/v1.0/precipitation'>Precipitation</a><br><br>"
    f"<a href='/api/v1.0/stations'>Stations</a><br><br>"
    f"<a href='/api/v1.0/tobs'>Tobs</a><br><br>"
    f"<a href='/api/v1.0/<start'>Start</a><br><br>"
    f"<a href='/api/v1.0/<start>/<end'>End</a><br>"
)


@app.route('/api/v1.0/precipitation')
def precipitation():
    results = session.query(Measurement.date, Measurement.prcp ).all()
    query_dict = {date: prcp for date, prcp in results}
    return jsonify(query_dict)


@app.route('/api/v1.0/stations')
def stations():
    results = session.query(Station.station, Station.name)
    query_dict = {stat: name for stat, name in results}
    return jsonify(query_dict)


@app.route('/api/v1.0/tobs')
def tobs():
    dates = session.query(Measurement.date).all()
    datelist = []
    for date in dates:
        datelist.append(date._asdict())
    datevalues = []
    for date in datelist:
        datevalues.append(date["date"])

    mostrecent = dt.date(1900, 1, 1)
    for date in datevalues:
        datesplit = date.split("-")
        currentdate = dt.date(int(datesplit[0]), int(datesplit[1]), int(datesplit[2]))
        if currentdate > mostrecent:
            mostrecent = currentdate
    oneyearago = mostrecent - dt.timedelta(days=365)

    dates = session.query(Measurement.station, Measurement.date, Measurement.tobs).filter(Measurement.date > oneyearago).all()
    diclist = []
    for date in dates:
        tobsdic = {"station": date[0], "date": date[1], "tobs": date[2]}
        diclist.append(tobsdic)
    return jsonify(diclist)

@app.route('/api/v1.0/<start>')
# def timeframe(start='2016-01-01'):
#     dates = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date >= start).all()
#     datelist = []
#     for date in dates:
#         datelist.append(dict(date=start, TMIN=date[0], TAVG=date[1], TMAX=date[2]))
#     return jsonify(datelist)

def start_only(start=None):
    """Return a list of min, avg, max for specific dates"""
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
   
    results= session.query(*sel).filter(Measurement.date >= start).all()
    temps = list(np.ravel(results))
    return jsonify(temps)



@app.route('/api/v1.0/<start>/<end>')
def timeframe_specific(start='2010-01-01', end='2017-01-01'):
    dates = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    datelist = []
    for date in dates:
        datelist.append(dict(start=start, end=end, TMIN=date[0], TAVG=date[1], TMAX=date[2]))
    return jsonify(datelist)

if __name__ == "__main__":
    app.run(debug=True)