from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import yfinance as yf

app = Dash(__name__)


period_choices = [
    "6mo",
    "1y",
    "2y",
    "5y",
    "10y",
    "ytd",
    "max",
]

stock_choices = ['TSLA', 'GOOGL', 'AAPL', 'AMZN']

app.layout = html.Div(
    children=[
        html.H1(children='Financial Advisor'),
        dcc.RadioItems(period_choices, period_choices[0], id="period"),
        dcc.Input(id="investment-amount", type='number'),
        dcc.Dropdown(
            stock_choices,
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
    try:
        df = (
            yf.download(selected_stocks, period=period)[['Close']]
            .droplevel(0, axis=1)
            .reset_index()
        )
    except ValueError:
        df = yf.download(selected_stocks, period=period)[['Close']].reset_index()

    df.iloc[:, 1:] = ((df.iloc[:, 1:].pct_change(1) + 1).cumprod() - 1).fillna(0)

    fig = px.line(
        df,
        x='Date',
        y=df.columns[1:],
        template="simple_white",
    )
    fig.update_traces(hovertemplate='%{y:.1%}')
    fig.update_layout(yaxis_tickformat=".0%")
    fig.update_layout(hovermode="x unified")

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
