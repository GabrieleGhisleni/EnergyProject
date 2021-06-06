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

    # cursor = connection.cursor()
    # query = """SELECT * from energy_installed_capacity"""
    # cursor.execute(query)
    # last = cursor.fetchall()
    # tmp = pd.DataFrame(last)
    # print(tmp)
    #return render(requests, 'Display/prediction.html', {'data':tmp})

def last_load(requests):
    engine = create_engine(f"mysql+pymysql://{RDS_USER}:{RDS_PSW}@{RDS_HOST}/energy")
    engine.connect()
    #date = datetime.datetime.today().strftime("%Y-%m-%d")
    date = (datetime.datetime.today()+datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    query = f"""select date,generation,energy from prediction_energy 
        where cast(prediction_energy.`date` as Date) = cast('{date}' as Date);"""
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
    fig.update_layout(title="Load ~ Renewable productions and Thermal on the date: " + dates[0].split(" ")[0],
                      legend=dict(orientation="h", yanchor="middle", y=1.02, xanchor="right", x=1),
                      # bgcolor="#B9D9EB"), #bordercolor="Black", borderwidth=2),
                      xaxis=dict(title="Hours",
                                 tickmode='array',
                                 tickvals=dates,
                                 ticktext=x_ticks,
                                 tick0=0.2,
                                 tickangle=30),
                      yaxis={'title': "Generation/consumption in  GW/H"},
                      margin={'l': 50, 'r': 50, 'b': 50, 't': 50, 'pad': 2},
                      # paper_bgcolor='white', plot_bgcolor='white',
                      width=1000, height=600,
                      template="gridon",
                      paper_bgcolor='rgb(235,235,235)')

    load = plot({'data': fig},
                output_type="div",include_plotlyjs=False, show_link=False, link_text="")

    return render(requests, "Display/prediction.html", context={'plot_div': load,
    'probability':[len(df),len(df)/7, dates[0],dates[-1],0.7,0.1,0.2,0.1,0.2,0.4,0.7,0.4,0.5,0.34,0.9,0.4,0.1,0.7,0.5,0.70,0.50,0.1,0.5]})

def home(requests):
    return render(requests, 'Display/home.html', {'data':"HOME"})

def about(requests):
    return render(requests, 'Display/about.html', {'data':"about"})

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