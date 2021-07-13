from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect
from django.contrib import messages
from .form import UserRegistrationForm
import numpy as np
import datetime as dt
from plotly.offline import plot
import plotly.graph_objs as go
import Code.meteo_managers as dbs
from plotly.subplots import make_subplots
import pandas as pd

def make_plot(dates, load, thermal, wind, hydro, photovoltaic, geothermal, biomass):
    fig = go.Figure()
    marker_load = dict(color='red', size=5, line=dict(color='red', width=2))
    fig.add_trace(go.Scatter(name="Load", x=dates, y=load, fill='tonexty', mode='lines+markers', marker=marker_load))
    fig.add_trace(go.Scatter(name="Thermal", x=dates, y=thermal, fill='tozeroy', stackgroup='one', hoverinfo='x+y'))
    fig.add_trace(go.Scatter(name="Photovoltaic", x=dates, y=photovoltaic, fill='tonexty', stackgroup='one', hoverinfo='x+y'))
    fig.add_trace(go.Scatter(name="Hydro", x=dates, y=hydro, fill='tonexty', stackgroup='one', hoverinfo='x+y'))
    fig.add_trace(go.Scatter(name="Wind", x=dates, y=wind, fill='tonexty', stackgroup='one', hoverinfo='x+y'))
    fig.add_trace(go.Scatter(name="Biomass", x=dates, y=biomass, fill='tonexty', stackgroup='one', hoverinfo='x+y'))
    fig.add_trace(go.Scatter(name="Geothermal", x=dates, y=geothermal, fill='tonexty', stackgroup='one', hoverinfo='x+y'))
    x_ticks = [date.split(" ")[1][:5] for date in dates]
    tickfont = dict(family='Old Standard TT, serif',size=18, color='black' )
    legend_dict = dict(orientation="h", yanchor="middle", y=1.01, xanchor="right", x=1.01, font = dict(size=20))
    xaxis_dict = dict(tickmode='array', tickvals=dates, ticktext=x_ticks, tick0=0.2, tickangle=30, dtick=0.5, tickfont=tickfont)
    yaxis_dict = dict(title=dict(text="Generation/consumption in  GW/H",font_size=25),
                      range=[0, 65], showgrid=True, tickfont=tickfont)
    margin_dict = dict(l=100, r=50, b=50, t=35, pad=7.5)

    fig.update_layout(legend=legend_dict,
                      xaxis=xaxis_dict, yaxis=yaxis_dict, margin=margin_dict, width=1400, height=600,
                      template="gridon", paper_bgcolor='rgb(240,248,255)')

    load = plot({'data': fig}, output_type="div", include_plotlyjs=False, show_link=False, link_text="")
    return load

def make_empty_plot():
    fig = go.Figure()
    fig.add_annotation(x=-1, y=0, text="No Data To Display Yet",
                       font=dict(family="sans serif, bold", size=45, color="crimson"),
                       showarrow=False, yshift=0)
    x, y = [-1], [0]
    for source in ['Load', 'Thermal', 'Photovoltaic', 'Hydro', 'Wind', 'Biomass', 'Geothermal']:
        fig.add_trace(go.Scatter(name=source, x=x, y=y, mode='lines'))

    xaxis_dict = dict(visible=False, showgrid=False)
    yaxis_dict = dict(visible=False, showgrid=False)
    margin_dict = dict(l=40, r=40, b=40, t=40, pad=7.5)
    fig.update_layout(xaxis=xaxis_dict, yaxis=yaxis_dict, margin=margin_dict, showlegend=False,
                      width=900, height=600, template="gridon", paper_bgcolor='rgba(255,10,10,4)')
    empty = plot({'data': fig}, output_type="div", include_plotlyjs=False, show_link=False, link_text="")
    return empty

def difference(load, thermal, wind, hydro, photovoltaic, geothermal, biomass):
    summation = np.array(wind) + np.array(thermal) + np.array(hydro) + np.array(photovoltaic) + np.array(geothermal) + np.array(biomass)
    differencess = (np.array(load) - summation).tolist()
    rounded = [round(i, 2) for i in differencess]
    hours = [iel for iel in range(23, 23-len(rounded),-1)]
    hours.reverse()
    res, tmp =[], {}
    for value in range(len(rounded)):
        tmp = {}
        tmp["obs"] = {}
        tmp["obs"]["v"] = rounded[value]
        tmp["obs"]["k"] = f"{hours[value]}h" if hours[value]>9 else f"0{hours[value]}h"
        res.append(tmp)
    return res

def get_data(day='today'):
    redis = dbs.RedisDB()
    data = redis.get_data(day=day)
    return data

def unroll_df(df, cat, groups, dates):
    if not df.empty:
        df['month'] = df[dates].dt.strftime("%B")
        df['hour'] = df[dates].dt.strftime("%H").astype('int')
        storage = []
        for unique in np.unique(df[cat]):
            temp = df.loc[df[cat] == unique, :].groupby(groups).mean().reset_index()
            temp[cat] = unique
            storage.append(temp)
        return pd.concat(storage)
    else: return pd.DataFrame()

def get_plots_data():
    db = dbs.MySqlDB()
    query_energy = "select energy_source as src, date, generation as y from energy_generation"
    query_load = "SELECT total_load as y, holiday, date from energy.energy_load"
    energy = db.query_from_sql_to_pandas(query_energy)
    load = db.query_from_sql_to_pandas(query_load)
    return energy,load

def make_energy_panel_plot(energy_df, load_df):
    titles = ['Load', 'Thermal & Hydro', 'Others Renewable']
    x_m, y_m = 'Hours of the day', 'Load - Generation in [GWH]'
    fig = make_subplots(rows=1, cols=3, print_grid=False, subplot_titles=titles, x_title=x_m, y_title=y_m, shared_yaxes=True)
    lined = dict(width=4)
    for src in np.unique(energy_df.src):
        if src == 'Hydro' or src == 'Thermal':
            fig.add_trace(go.Scatter(x=energy_df.loc[energy_df.src == src].hour, y=energy_df.loc[energy_df.src == src].y,
                           name=src, mode='lines', showlegend=False, line=lined), row=1, col=2)
        else:
            fig.add_trace(go.Scatter(x=energy_df.loc[energy_df.src == src].hour, y=energy_df.loc[energy_df.src == src].y,
                           name=src, mode='lines',showlegend=True,line=lined), row=1, col=3)

    fig.add_trace(go.Scatter(x=load_df.groupby('hour').mean().reset_index().hour, name='load',showlegend=False,
                             y=load_df.groupby('hour').mean().reset_index().y, mode='lines',line=lined), row=1, col=1)

    margin_dict = dict(l=100, r=75, b=75, t=60, pad=7.5)
    yaxis_dict = dict(zeroline=False, tickvals=[i for i in range(0, 45, 2)], ticktext=[i for i in range(0, 45, 2)])
    xaxis_dict = dict(tickvals=[i for i in range(0, 24)], tickmode='array', tick0=0.2, tickangle=90, zeroline=False,
                      dtick=0.5, showgrid=False, ticktext=[f"0{str(i)}" if i < 10 else str(i) for i in range(0, 24)])
    for i in range(1, 4): fig.update_xaxes(xaxis_dict, row=1, col=i)
    for i in range(1, 4): fig.update_yaxes(yaxis_dict, row=1, col=i)
    legend_dict = dict(yanchor="middle", y=0.89, xanchor="right", x=1.0, font = dict(size=20))
    fig.update_layout(height=700, width=1400, template='gridon', paper_bgcolor='rgb(240,248,255)',
                      margin=margin_dict, legend=legend_dict)
    fig.update_annotations(font_size=30, font_family='italic')
    return plot({'data': fig}, output_type="div", include_plotlyjs=False, show_link=False, link_text="")

def make_load_panel_plot(load_df):
    titles = ['Load on Holiday', 'Load on Sunday', 'Load on Saturday', 'Load during Weeks']
    x_m, y_m = 'Hours of the day', 'Load - in [GWH]'
    lined = dict(width=4)
    fig = make_subplots(rows=1, cols=4, print_grid=False, subplot_titles=titles, x_title=x_m, y_title=y_m, shared_yaxes=True)
    fig.add_trace(go.Scatter(x=load_df.loc[load_df.holiday == 'holiday'].hour,
                             y=load_df.loc[load_df.holiday == 'holiday'].y, name='Holiday', mode='lines', line=lined), row=1, col=1)
    fig.add_trace(go.Scatter(x=load_df.loc[load_df.holiday == 'sunday'].hour,
                             y=load_df.loc[load_df.holiday == 'sunday'].y, name='Sunday', mode='lines', line=lined), row=1, col=2)
    fig.add_trace(go.Scatter(x=load_df.loc[load_df.holiday == 'saturday'].hour,
                             y=load_df.loc[load_df.holiday == 'saturday'].y, name='Saturday', mode='lines', line=lined), row=1, col=3)
    fig.add_trace(go.Scatter(x=load_df.loc[load_df.holiday == 'no'].hour,
                             y=load_df.loc[load_df.holiday == 'no'].y, name='Weeks', mode='lines', line=lined), row=1, col=4)
    margin_dict = dict(l=100, r=75, b=75, t=60, pad=7.5)
    xaxis_dict = dict(tickvals=[i for i in range(0, 24)], tickmode='array', tick0=0.2, tickangle=90, zeroline=False,
                      dtick=0.5, showgrid=False, ticktext=[f"0{str(i)}" if i < 10 else str(i) for i in range(0, 24)])
    for i in range(1, 5): fig.update_xaxes(xaxis_dict, row=1, col=i)
    for i in range(1, 5): fig.update_yaxes(dict(zeroline=False), row=1, col=i)
    fig.update_layout(height=600, width=1500, template='gridon', paper_bgcolor='rgb(240,248,255)', showlegend=False, margin=margin_dict)
    fig.update_annotations(font_size=30, font_family='italic')
    return plot({'data': fig}, output_type="div", include_plotlyjs=False, show_link=False, link_text="")


def today_pred(requests):
    data = get_data('today')
    if not data['load']: return render(requests, "Display/prediction.html", context=dict(plot_div=make_empty_plot(), day='Today', probability=[]))
    else:
        fig = make_plot(dates=data["dates"], load=data["load"], thermal=data["thermal"], wind=data["wind"], hydro=data["hydro"],
                    photovoltaic=data["photovoltaic"], geothermal=data["geothermal"], biomass=data["biomass"])
        differences = difference(data['load'], data["thermal"], data["wind"], data["hydro"], data["photovoltaic"], data["geothermal"], data["biomass"])
        today_s = dt.datetime.now().strftime("%B, %d-%Y")
        context = dict(plot_div=fig, day='Today', probability=differences, day_s=today_s)
        return render(requests, "Display/prediction.html", context)

def tomorrow_pred(requests):
    data = get_data(day='tomorrow')
    if not data['load']: return render(requests, "Display/prediction.html", context=dict(plot_div=make_empty_plot(), day='Today', probability=[]))
    else:
        fig = make_plot(dates=data["dates"], load=data["load"], thermal=data["thermal"], wind=data["wind"], hydro=data["hydro"],
                        photovoltaic=data["photovoltaic"], geothermal=data["geothermal"], biomass=data["biomass"])
        differences = difference(data['load'], data["thermal"], data["wind"], data["hydro"], data["photovoltaic"], data["geothermal"], data["biomass"])
        tomorrow_s = (dt.datetime.now()+dt.timedelta(days=1)).strftime("%B, %d-%Y")
        context = dict(plot_div=fig, day='Tomorrow', probability=differences, day_s=tomorrow_s)
        return render(requests, "Display/prediction.html", context)

def home(requests):
    return render(requests, 'Display/home.html', {'today-prediction': "HOME"})

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created, from now on you will receive an email each time the prediction are update!")
            return redirect("today")
    else:  form = UserRegistrationForm()
    return render(request, 'Display/newsletter.html', {"form": form})

def infographic(requests):
    energy, load = get_plots_data()
    energies = unroll_df(energy, cat='src', groups='hour', dates='date')
    loads = unroll_df(load, cat='holiday', groups='hour', dates='date')
    if not energies.empty and not loads.empty: first_panel = make_energy_panel_plot(energies, loads)
    else: first_panel = make_empty_plot()
    if not loads.empty: second_panel= make_load_panel_plot(loads)
    else: second_panel = make_empty_plot()
    context = dict(plot_div=first_panel, plot_load=second_panel)
    return render(requests, "Display/infos.html", context)


@api_view(['GET'])
def Energy_Full_Rest_API(requests):
    """
    We allow to retrive our prediction according to the data and according to the type of energy that you are interested in.
    By default it will return the prediction of the day.

    You can specify two parameters:

    -  `energy`  : [load, thermal, wind, photovoltaic, biomass, geothermal, hydro]
    -  `format`  : [json, api]
    -  `date`    : format %Y-%m-%d

    Is also possible to retrive a range of date as `date1, date2`.

    First Example:
    /api-auth/?format=json&energy=load,wind&date=2021-05-06

    Second Example:
    /api-auth/?format=api&energy=load&date=2021-05-06,2021-06-10

    To come back to the website click on the navbar brand 'Energy Project - HOME'.
    """
    db = dbs.MySqlDB()
    date = requests.query_params.get('date')
    energy_source = requests.query_params.get('energy')
    for params in requests.query_params:
        paramss = ["energy", "date", "format"]
        unknown_params = {'unknown parameter': f"choose available are: {paramss}"}
        if params not in paramss: return Response(unknown_params, status=status.HTTP_400_BAD_REQUEST)

    check_energy = {"load", "thermal", "wind", "photovoltaic", "biomass", "geothermal", "hydro"}
    query_add = " where "
    if energy_source:
        bad_request_msg_energy = {'energy': 'not found the source energy that you are asking for'}
        comma = energy_source.find(",")
        if comma != -1:
            i = 0
            for en in energy_source.split(","):
                if en not in check_energy: return Response(bad_request_msg_energy, status=status.HTTP_400_BAD_REQUEST)
                else:
                    if i == 0: query_add = query_add + f" (energy = '{en}' "
                    else: query_add = query_add + f" or energy = '{en}' "
                i += 1
        else:
            if energy_source not in check_energy: return Response(bad_request_msg_energy, status=status.HTTP_400_BAD_REQUEST)
            else: query_add = query_add + f"( energy = '{energy_source}' "

    if query_add != " where ": query_add = query_add.rstrip() + " )"
    if date:
        bad_request_msg_date = {'date': "Something went wrong with the date, are in format '%Y-%m-%d' ?"}
        if query_add == " where ": query_add = query_add + "( cast(prediction_energy.`date` as Date)  "
        else:   query_add = query_add + " and ( cast(prediction_energy.`date` as Date) "
        comma = date.find(",")
        if comma != -1:
            if len(date.split(",")) > 2: return Response(bad_request_msg_date,  status=status.HTTP_400_BAD_REQUEST)
            for en in date.split(","):
                try: date.datetime.strptime(en, "%Y-%m-%d")
                except Exception: return Response(bad_request_msg_date,  status=status.HTTP_400_BAD_REQUEST)
            if date.datetime.strptime(date.split(',')[0], "%Y-%m-%d") <= date.datetime.strptime(date.split(',')[1], "%Y-%m-%d"):
                first, second = date.split(',')[0], date.split(',')[1]
            else:  first, second = date.split(',')[1], date.split(',')[0]
            query_add += f"BETWEEN cast('{first}' as Date)  and cast('{second}' as Date)"
        else:
            try:
                dt.datetime.strptime(date, "%Y-%m-%d")
                query_add += f" = cast('{date}' as Date) "
            except Exception: return Response(bad_request_msg_date, status=status.HTTP_400_BAD_REQUEST)
        query_add = query_add + ")"

    today = (dt.datetime.today()).strftime("%Y-%m-%d")
    query = "select date, generation, energy from energy.prediction_energy" + query_add
    if not date and energy_source:
        query = query + f" and (cast(prediction_energy.`date` as Date) = cast('{today}' as Date))"
    if not date and not energy_source:
        # query = f"""select date,generation,energy from energy.prediction_energy
        #           where cast(prediction_energy.`date` as Date) = cast('{today}' as Date)"""
        return Response({'energy': '[load,wind,hydro,photovoltaic,biomass,thermal, geothermal]',
                         'date': 'format %Y-%m-%d'}, status=status.HTTP_200_OK)
    df = db.query_from_sql_to_pandas(query, dates='date')
    df.sort_values(['date'], inplace=True)
    return Response(df.to_dict(), status=status.HTTP_200_OK)




