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

    # title = f"""<b>Energy Predictions for {dates[0].split(" ")[0]}</b>"""
    # title_dict = dict(size=35, family='Bold-Courier', color='black')
    legend_dict = dict(orientation="h", yanchor="middle", y=1.01, xanchor="right", x=1.01)
    xaxis_dict = dict(tickmode='array', tickvals=dates, ticktext=x_ticks, tick0=0.2, tickangle=30, dtick=0.5)
    yaxis_dict = dict(title="Generation/consumption in  GW/H", range=[0, 65], showgrid=True)
    margin_dict = dict(l=75, r=50, b=50, t=35, pad=7.5)

    fig.update_layout(legend=legend_dict,
                      xaxis=xaxis_dict, yaxis=yaxis_dict, margin=margin_dict, width=1400, height=600,
                      template="gridon", paper_bgcolor='rgb(245,245,245)') # ,title=title, title_font=title_dict,

    load = plot({'data': fig}, output_type="div", include_plotlyjs=False, show_link=False, link_text="")
    return load

def make_empty_plot():
    fig = go.Figure()
    fig.add_annotation(x=-1, y=25, text="No Data to Display Yet",
                       font=dict(family="sans serif", size=35, color="crimson"),
                       showarrow=False, yshift=10)
    x, y = [-1], [0]
    for source in ['Load', 'Thermal', 'Photovoltaic', 'Hydro', 'Wind', 'Biomass', 'Geothermal']:
        fig.add_trace(go.Scatter(name=source, x=x, y=y, mode='lines'))
    title = f"""<b>Load ~ Renewable productions and Thermal</b>"""
    title_dict = dict(size=18, family='Bold-Courier', color='crimson')
    legend_dict = dict(orientation="h", yanchor="middle", y=1.01, xanchor="right", x=1.01)
    xaxis_dict = dict(title="Hours", tickmode='array', tick0=0.2, tickangle=30, dtick=0.5, showgrid=False)
    yaxis_dict = dict(title="Generation/consumption in  GW/H", range=[0, 60], showgrid=False)
    margin_dict = dict(l=75, r=50, b=75, t=100, pad=7.5)
    fig.update_layout(title=title, title_font=title_dict, legend=legend_dict,
                      xaxis=xaxis_dict, yaxis=yaxis_dict, margin=margin_dict, width=800, height=600,
                      template="gridon", paper_bgcolor='rgb(245,245,245)')
    load = plot({'data': fig}, output_type="div", include_plotlyjs=False, show_link=False, link_text="")
    return load

def difference(load, thermal, wind, hydro, photovoltaic, geothermal, biomass):
    summation = np.array(wind) + np.array(thermal) + np.array(hydro) + np.array(photovoltaic) + np.array(geothermal) + np.array(biomass)
    differencess = (np.array(load) - summation).tolist()
    return [round(i, 2) for i in differencess]

def get_data(day='today'):
    redis = dbs.RedisDB()
    data = redis.get_data(day=day)
    return data

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

def home(requests):
    return render(requests, 'Display/home.html', {'today-prediction': "HOME"})

def about(requests):
    return render(requests, 'Display/about.html', {'today-prediction': "about"})

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created, from now on you will receive an email each time the prediction are update!")
            return redirect("today")
    else:  form = UserRegistrationForm()
    return render(request, 'Display/newsletter.html', {"form": form})
