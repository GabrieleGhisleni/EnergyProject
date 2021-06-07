from django.shortcuts import render
from django.db import connection
from django.shortcuts import render
from django.db.models import Q
import pandas as pd
from plotly.offline import plot
import plotly.graph_objs as go
import datetime
from sqlalchemy import create_engine
import os
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from .form import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from KEYS.config import RDS_USER, RDS_PSW,RDS_HOST


def today_pred(requests):
    engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
    engine.connect()
    today = (datetime.datetime.today()).strftime("%Y-%m-%d")
    query = f"""select date,generation,energy from prediction_energy 
    where cast(prediction_energy.`date` as Date) = cast('{today}' as Date)
    order by idprediction_energy desc limit 0,168;"""
    df = pd.read_sql_query(query, engine, parse_dates=["date"])
    fig = go.Figure()

    #dates = df["date"].dt.strftime("%Y-%m-%d %H:%M").unique()

    dates = df["date"].dt.strftime("%Y-%m-%d %H:%M").unique()
    fig.add_trace(go.Scatter(name="Load", x=dates, y=df.generation[df["energy"] == "load"], fill='tonexty',
                             mode='lines+markers',marker=dict(color='red',  size=5,
                                 line=dict( color='red',width=2 ),)))  # fill down to xaxis
    fig.add_trace(go.Scatter(name="Thermal", x=dates, y=df.generation[df["energy"] == "thermal"], fill='tozeroy',
                             stackgroup='one', hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(
        go.Scatter(name="Photovoltaic", x=dates, y=df.generation[df["energy"] == "photovoltaic"], fill='tonexty',
                   stackgroup='one', hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(
        go.Scatter(name="Hydro", x=dates, y=df.generation[df["energy"] == "hydro"], fill='tonexty', stackgroup='one',
                   hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(
        go.Scatter(name="Wind", x=dates, y=df.generation[df["energy"] == "wind"], fill='tonexty', stackgroup='one',
                   hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(go.Scatter(name="Biomass", x=dates, y=df.generation[df["energy"] == "biomass"], fill='tonexty',
                             stackgroup='one', hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(go.Scatter(name="Geothermal", x=dates, y=df.generation[df["energy"] == "geothermal"], fill='tonexty',
                             stackgroup='one', hoverinfo='x+y'))  # fill to trace0 y

    x_ticks = [(date.split(" "))[1] for date in dates]
    fig.update_layout(title="<b>Load ~ Renewable productions and Thermal on the date: " + dates[0].split(" ")[0]+"</b>",
                      title_font=dict(size=18, family='Bold-Courier', color='crimson'),
                      legend=dict(orientation="h", yanchor="middle", y=1.01, xanchor="right", x=1.01),
                      # bgcolor="#B9D9EB"), #bordercolor="Black", borderwidth=2),
                      xaxis=dict(title="Hours",
                                 tickmode='array',
                                 tickvals=dates,
                                 ticktext=x_ticks,
                                 tick0=0.2,
                                 tickangle=30,
                                 dtick=0.5,
                                 showgrid=False),
                      yaxis= dict(title="Generation/consumption in  GW/H",
                                  range= [0,50],
                                  showgrid= False   ),
                      margin={'l': 75, 'r': 50, 'b': 75, 't': 100, 'pad': 7.5},
                      # paper_bgcolor='white', plot_bgcolor='white',
                      width=1000, height=600,
                      template="gridon",
                      paper_bgcolor='rgb(245,245,245)')

    load = plot({'data': fig},
                output_type="div",include_plotlyjs=False, show_link=False, link_text="")

    return render(requests, "Display/prediction.html", context={'plot_div': load,
    'probability':[len(df),len(df)/7, dates[0],dates[-1],0.7,0.1,0.2,0.1,0.2,0.4,0.7,0.4,0.5,0.34,0.9,0.4,0.1,0.7,0.5,0.70,0.50,0.1,0.5]})

def tomorrow_pred(requests):
    engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
    engine.connect()
    tomorrow = (datetime.datetime.today()+datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    date = (datetime.datetime.today()+datetime.timedelta(days=2)).strftime("%Y-%m-%d")

    query = f"""select date,generation,energy from prediction_energy 
    where cast(prediction_energy.`date` as Date) = cast('{tomorrow}' as Date)
    order by idprediction_energy desc limit 0,168;"""
    df = pd.read_sql_query(query, engine, parse_dates=["date"])
    fig = go.Figure()

    #dates = df["date"].dt.strftime("%Y-%m-%d %H:%M").unique()

    dates = df["date"].dt.strftime("%Y-%m-%d %H:%M").unique()
    fig.add_trace(go.Scatter(name="Load", x=dates, y=df.generation[df["energy"] == "load"], fill='tonexty',
                             mode='lines+markers',marker=dict(color='red',  size=5,
                                 line=dict( color='red',width=2 ),)))  # fill down to xaxis
    fig.add_trace(go.Scatter(name="Thermal", x=dates, y=df.generation[df["energy"] == "thermal"], fill='tozeroy',
                             stackgroup='one', hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(
        go.Scatter(name="Photovoltaic", x=dates, y=df.generation[df["energy"] == "photovoltaic"], fill='tonexty',
                   stackgroup='one', hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(
        go.Scatter(name="Hydro", x=dates, y=df.generation[df["energy"] == "hydro"], fill='tonexty', stackgroup='one',
                   hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(
        go.Scatter(name="Wind", x=dates, y=df.generation[df["energy"] == "wind"], fill='tonexty', stackgroup='one',
                   hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(go.Scatter(name="Biomass", x=dates, y=df.generation[df["energy"] == "biomass"], fill='tonexty',
                             stackgroup='one', hoverinfo='x+y'))  # fill to trace0 y
    fig.add_trace(go.Scatter(name="Geothermal", x=dates, y=df.generation[df["energy"] == "geothermal"], fill='tonexty',
                             stackgroup='one', hoverinfo='x+y'))  # fill to trace0 y

    x_ticks = [(date.split(" "))[1] for date in dates]
    fig.update_layout(title="<b>Load ~ Renewable productions and Thermal on the date: " + dates[0].split(" ")[0]+"</b>",
                      title_font=dict(size=18, family='Bold-Courier', color='black'),
                      legend=dict(orientation="h", yanchor="middle", y=1.01, xanchor="right", x=1.01),
                      # bgcolor="#B9D9EB"), #bordercolor="Black", borderwidth=2),
                      xaxis=dict(title="Hours",
                                 tickmode='array',
                                 tickvals=dates,
                                 ticktext=x_ticks,
                                 tick0=0.2,
                                 tickangle=30,
                                 dtick=0.5,
                                 showgrid=False),
                      yaxis= dict(title="Generation/consumption in  GW/H",
                                  range= [0,50],
                                  showgrid= False   ),
                      margin={'l': 75, 'r': 50, 'b': 75, 't': 100, 'pad': 7.5},
                      # paper_bgcolor='white', plot_bgcolor='white',
                      width=1000, height=600,
                      template="gridon",
                      paper_bgcolor='rgb(245,245,245)')

    load = plot({'data': fig},
                output_type="div",include_plotlyjs=False, show_link=False, link_text="")

    return render(requests, "Display/prediction.html", context={'plot_div': load,
    'probability':[len(df),len(df)/7, dates[0],dates[-1],0.7,0.1,0.2,0.1,0.2,0.4,0.7,0.4,0.5,0.34,0.9,0.4,0.1,0.7,0.5,0.70,0.50,0.1,0.5]})

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def DownloadCenter(requests):
    engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
    engine.connect()
    date = requests.query_params.get('date')
    energy_source = requests.query_params.get('energy')
    query = f"""select date,generation,energy  from energy.prediction_energy """
    df = pd.read_sql_query(query, engine, parse_dates=["date"])
    api_urls= df.to_dict()
    return Response()

def home(requests):
    return render(requests, 'Display/home.html', {'today-prediction':"HOME"})

def about(requests):
    return render(requests, 'Display/about.html', {'today-prediction':"about"})

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(request,
                             """Account created, from now on you will receive an email 
                             each time the prediction  are update!""")
            return redirect("data")
    else:
        form = UserRegistrationForm()
    return render(request, 'Display/newsletter.html', {"form":form})