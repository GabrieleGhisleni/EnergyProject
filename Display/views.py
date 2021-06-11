from django.http import JsonResponse
from rest_framework.decorators import api_view,renderer_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import render
from django.db import connection
from django.shortcuts import render
from django.db.models import Q
import pandas as pd
from plotly.offline import plot
import plotly.graph_objs as go
import datetime,json,os
from sqlalchemy import create_engine
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from .form import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from KEYS.config import RDS_USER, RDS_PSW,RDS_HOST
import numpy as np

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

    load = plot({'data': fig}, output_type="div",include_plotlyjs=False, show_link=False, link_text="")
    context = dict(plot_div=load, day='Today', probability=[1,2])
    return render(requests, "Display/prediction.html", context)

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
    load = plot({'data': fig},  output_type="div",include_plotlyjs=False, show_link=False, link_text="")
    g,res = df[df['energy']!='load'].groupby('date', as_index=False),[]
    for name, group in (g):
        tmp = pd.DataFrame(group.sum())
        columns = list(tmp.index)[0:]
        valori = list(tmp[0][0:].values)
        df_2 = pd.DataFrame([valori], columns=columns)
        df_2.insert(loc=0, column='date', value=name)
        res.append(df_2)
    final_sources = pd.concat(res)
    diff = (df.generation[df['energy'] == 'load'].values - final_sources['generation'].values)
    context = dict(plot_div=load, day='Tomorrow', probability=[np.round(diffi,2) for diffi in diff])
    return render(requests, "Display/prediction.html", context)

@api_view(['GET'])
#@renderer_classes([JSONRenderer])
def Energy_Full_Rest_API(requests):
    """
    We allow to retrive our prediction according to the data and according to the type of energy that you are interested in.
    By default it will return the prediction of the day.

    You can specify two parameters:

    -  `energy`  : [load, thermal, wind, photovoltaic, biomass, geothermal, hydro]
    -  `date`    : format %Y-%m-%d

    Is also possible to retrive a range of date as `date1, date2`.

    First Example:
    /api-auth/?format=api&energy=load,wind&date=2021-05-06

    Second Example:
    /api-auth/?format=api&energy=load&date=2021-05-06,2021-06-10

    To come back to the website click on the navbar brand 'Energy Project - HOME'.
    """
    engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
    engine.connect()
    date = requests.query_params.get('date')
    energy_source = requests.query_params.get('energy')
    for params in requests.query_params:
        unknown_params = {'unknown parameter' : "choose available are: [`enery`, `date`]"}
        if params != 'energy' and params != 'date': return (Response(unknown_params, status=status.HTTP_400_BAD_REQUEST))

    check_energy = {"load", "thermal", "wind", "photovoltaic", "biomass", "geothermal", "hydro"}
    query_add = " where "
    dates,energy_to_add = " where ", " where "
    if energy_source:
        bad_request_msg_energy= {'energy': 'not found the source energy that you are asking for'}
        comma= energy_source.find(",")
        if comma != -1:
            i=0
            for en in energy_source.split(","):
                if en not in check_energy:  return (Response(bad_request_msg_energy,status=status.HTTP_400_BAD_REQUEST))
                else:
                    if i==0: query_add = query_add+ f" (energy = '{en}' "
                    else: query_add = query_add+ f" or energy = '{en}' "
                i+=1
        else:
            if energy_source not in check_energy:  return (Response(bad_request_msg_energy,status=status.HTTP_400_BAD_REQUEST))
            else: query_add = query_add+ f"( energy = '{energy_source}' "

    if query_add != " where ": query_add= query_add.rstrip() +" )"
    if date:
        bad_request_msg_date= {'date': "Something went wrong with the date, are in format '%Y-%m-%d'"}
        if query_add == " where ":            query_add = query_add + "( cast(prediction_energy.`date` as Date)  "
        else:   query_add = query_add + " and ( cast(prediction_energy.`date` as Date) "
        comma = date.find(",")
        if comma != -1:
            if len(date.split(","))>2: return (Response(bad_request_msg_date,  status=status.HTTP_400_BAD_REQUEST))
            for en in date.split(","):
                try:  datetime.datetime.strptime(en,"%Y-%m-%d")
                except: return (Response(bad_request_msg_date,  status=status.HTTP_400_BAD_REQUEST))
            if datetime.datetime.strptime(date.split(',')[0],"%Y-%m-%d") <= datetime.datetime.strptime(date.split(',')[1],"%Y-%m-%d"):
                first,second = date.split(',')[0], date.split(',')[1]
            else:  first,second = date.split(',')[1], date.split(',')[0]
            query_add += f"BETWEEN cast('{first}' as Date)  and cast('{second}' as Date)"
        else:
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
                query_add+= f" = cast('{date}' as Date) "
            except:  return (Response(bad_request_msg_date, status=status.HTTP_400_BAD_REQUEST))
        query_add = query_add+")"

    today = (datetime.datetime.today()).strftime("%Y-%m-%d")
    query = "select date,generation,energy from energy.prediction_energy" + query_add
    if not date and energy_source:
        query = query + f" and (cast(prediction_energy.`date` as Date) = cast('{today}' as Date))"
    if not date and not energy_source:
        query = f"""select date,generation,energy from energy.prediction_energy
                  where cast(prediction_energy.`date` as Date) = cast('{today}' as Date)"""
    df = pd.read_sql_query(query, engine, parse_dates=["date"])
    df.sort_values(['date'], inplace=True)
    print(query)
    return Response(df.to_dict(), status=status.HTTP_200_OK)


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