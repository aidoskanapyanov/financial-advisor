from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import yfinance as yf


app = Dash(__name__)


period_options = [
    "6mo",
    "1y",
    "2y",
    "5y",
    "10y",
    "ytd",
    "max",
]


app.layout = html.Div(
    children=[
        html.H1(children='Financial Advisor'),
        dcc.RadioItems(period_options, period_options[0], id="period"),
        dcc.Input(id="investment-amount", type='number'),
        dcc.Dropdown(
            ['TSLA', 'GOOGL', 'AAPL', 'AMZN'],
            ['TSLA', 'GOOGL'],
            multi=True,
            id="stocks",
        ),
        dcc.Graph(id='my-output'),
    ]
)


@app.callback(
    Output('my-output', 'figure'),
    Input('period', 'value'),
    Input('investment-amount', 'value'),
    Input('stocks', 'value'),
)
def update_output_div(period, investment_amount, selected_stocks):
    df = (
        yf.download(selected_stocks, period=period)[['Close']]
        .droplevel(0, axis=1)
        .reset_index()
    )
    return px.line(df, x='Date', y=df.columns[1:])


if __name__ == '__main__':
    app.run_server(debug=True)
