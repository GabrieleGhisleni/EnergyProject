import pandas as pd
import numpy as np
import os

def calcEasterDate(year):
    special_years = ['1954', '1981', '2049', '2076']
    specyr_sub = 7
    a = year % 19
    b = year % 4
    c = year % 7
    d = (19 * a + 24) % 30
    e = ((2 * b) + (4 * c) + (6 * d) + 5) % 7
    if year in special_years:
        dateofeaster = (22 + d + e) - specyr_sub
    else:
        dateofeaster = 22 + d + e
    if dateofeaster > 31:
        if (dateofeaster-31) >= 10:
            return ("{}-04".format(dateofeaster - 31))
        else:
            dateofeaster = "0"+str(dateofeaster-31)
            return  ("{}-04".format(dateofeaster))
    else:
        return ("{}-03".format(dateofeaster))

def create_calendar():
    df = pd.DataFrame()
    tmp = pd.date_range('2021-01-01', '2050-01-01', freq='D').to_series()
    df["day"] = tmp.dt.day_name()
    df.reset_index(inplace=True)
    df["holiday"] = np.where(df["day"] == "Sunday", "yes", "no")
    df["holiday"].loc[df["day"] == "Saturday"] = "half"
    it = {"01-01", "06-01", "25-04", "01-05", "02-06", "15-08", "01-10", "08-12", "25-12", "26-12"}
    ## Easter:
    tmp_easter = []
    for year in range(2021,2051):
        date = calcEasterDate(year)
        if date.startswith("31"):
            date = "01-04"
        else:
            date = str(int(date.split("-")[0]) + 1) + "-" +date.split("-")[1]
        tmp_easter.append((str(year)+"-"+date))
    for pasqua in tmp_easter:
        df["holiday"].loc[df["index"] == pasqua] = "yes"
    # Other holidays
    tmp = []
    for row in df["index"].dt.strftime('%m-%d'):
        if row in it:
            tmp.append("Yes")
        else:
            tmp.append("No")
    tmp = pd.Series(tmp)
    df["holiday"].loc[tmp == "Yes"] = "yes"
    df.columns = ["Date", "DayName", "Holiday"]
    return df

if __name__ == "__main__":
    if not os.path.exists("italian-holiday-calendar.csv"):
        create_calendar().to_csv("italian-holiday-calendar.csv", index=False)