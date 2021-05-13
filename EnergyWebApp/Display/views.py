from django.shortcuts import render
from django.db import connection
from django.shortcuts import render
from django.db.models import Q
import pandas as pd
from plotly.offline import plot
from plotly.graph_objs import Scatter, Area
import datetime
from sqlalchemy import create_engine
import os


    # cursor = connection.cursor()
    # query = """SELECT * from energy_installed_capacity"""
    # cursor.execute(query)
    # last = cursor.fetchall()
    # tmp = pd.DataFrame(last)
    # print(tmp)
    #return render(requests, 'Display/prediction.html', {'data':tmp})

def last_load(requests):
    engine = create_engine("mysql+pymysql://root:{}@localhost/energy".format(os.environ.get("SQL")))
    engine.connect()
    query = f"""
    SELECT * from energy_load
    WHERE date='{datetime.date.today()}'
    """
    df= pd.read_sql_query(query, engine)
    x = range(0,24)
    x_data = [100,1,2,3]
    y_data = [x**2 for x in x_data]
    hours = list(range(0,24))
    prova_load= [29072.151095238096, 26971.04792099567, 25661.323884920635, 25185.131571428574, 25158.297369047617, 25544.67380158729, 27210.593626984126, 29960.4473445166, 32865.96649206349, 35472.64432539683, 36016.216599206346, 35717.81636904762, 34688.73887012986, 33051.572695887444, 32233.3469119769, 32227.615845238088, 32512.898989177487, 35772.4585515873, 37036.787011904766, 37939.69539177488, 36448.85898412698, 33571.459523809535, 30953.17539033189, 28158.819523809525]
    prova_generation = [8.46,  8.24,  8.03,  7.78,  7.58,  7.76,  9.51, 12.88, 15.51, 17.28, 19.67, 20.65, 20.58,19.36, 17.76, 15.17, 14.08, 14.44, 14.43, 13.62, 12.00,10.03,  8.88,  8.12,]
    data = [Scatter(x=hours, y=prova_load,
                mode='lines',
                opacity=0.8, marker_color='green')]

    load = plot({
    'data': data,
    'layout': dict(title=f"Predicted load for {datetime.date.today()}", 
    xaxis={'title': "Hours"}, 
    yaxis={'title': "Load in GW/H"},
    margin={'l': 55,'r': 50,'b': 50,'t': 50,'pad': 10},
    paper_bgcolor= 'white',
    plot_bgcolor= 'white')}, 
    output_type="div")  

    data = [Scatter(x=hours, y=prova_generation,
                mode='lines',
                opacity=0.8, marker_color='red')]

    production = plot({
    'data': data,
    'layout': dict(title=f"Predicted generation for {datetime.date.today()}", 
    xaxis={'title': "Hours"}, 
    yaxis={'title': "Generation in GW/H"},
    margin={'l': 55,'r': 50,'b': 50,'t': 50,'pad': 10},
    paper_bgcolor= 'white',
    plot_bgcolor= 'white')}, 
    output_type="div") 


    return render(requests, "Display/prediction.html", context={'plot_div': load, 'load':production,
    'probability':[0.3,0.1,1,0.4,0.5,0.7,0.1,0.2,0.1,0.2,0.4,0.7,0.4,0.5,0.34,0.9,0.4,0.1,0.7,0.5,0.70,0.50,0.1,0.5]})

def home(requests):
    return render(requests, 'Display/home.html', {'data':"HOME"})
def about(requests):
    return render(requests, 'Display/about.html', {'data':"about"})