import pandas as pd
from dash import Dash, dcc, html
import sqlite3

# import data
con = sqlite3.connect("C:/Data_analysis/timsQC/history.sqlite")
cur = con.cursor()
data = pd.read_sql_query(f"SELECT * FROM InstrumentParameterHistory", con)
data()
#data = (
#    pd.read_csv("avocado.csv")
#    .query("type == 'conventional' and region == 'Albany'")
#    .assign(Date=lambda data: pd.to_datetime(data["Date"], format="%Y-%m-%d"))
#    .sort_values(by="Date")
#)

app = Dash(__name__)

# App Layout

app.layout = html.Div(
    children=[
        html.H1(children="Avocado Analytics"),
        html.P(
            children=(
                "Analyze the behavior of avocado prices and the number"
                " of avocados sold in the US between 2015 and 2018"
            ),
        ),
        dcc.Graph(
            figure={
                "data": [
                    {
                        "x": data["Date"],
                        "y": data["AveragePrice"],
                        "type": "lines",
                    },
                ],
                "layout": {"title": "Average Price of Avocados"},
            },
        ),
        dcc.Graph(
            figure={
                "data": [
                    {
                        "x": data["Date"],
                        "y": data["Total Volume"],
                        "type": "lines",
                    },
                ],
                "layout": {"title": "Avocados Sold"},
            },
        ),
    ]
)

# ...

if __name__ == "__main__":
    app.run_server(debug=True)