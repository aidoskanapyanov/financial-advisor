from dash import Dash, html, dcc, Input, Output, ctx
import pandas as pd
import plotly.express as px
import yfinance as yf
import dash_bootstrap_components as dbc
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from pypfopt import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt.exceptions import OptimizationError
from io import StringIO
import sys
from loguru import logger

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)


period_choices = [
    # "6mo",
    # "1y",
    "2y",
    "5y",
    "10y",
    # "ytd",
    "max",
]
default_period_choice = "2y"

stock_choices = ["TSLA", "GOOGL", "AAPL", "AMZN"]
default_stock_choice = "TSLA"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(
                    children="Financial Advisor", className="w-75 text-center my-2"
                ),
                html.P("Choose period for optimization:", className="mb-0"),
                dcc.RadioItems(
                    period_choices,
                    default_period_choice,
                    id="period",
                    className="d-flex justify-content-evenly w-25 my-2",
                ),
                html.P("Set the investment amount:", className="mb-0"),
                dcc.Input(
                    id="investment-amount",
                    type="number",
                    placeholder="100000",
                    required=True,
                    className="my-2",
                    style={"width": "10rem"},
                ),
                html.Button(
                    'Calculate asset allocation', id='calculate-btn', n_clicks=0
                ),
                html.P("Select the stocks for optimization:", className="mb-0"),
                html.Div(
                    dcc.Dropdown(
                        stock_choices,
                        [default_stock_choice],
                        multi=True,
                        id="stocks",
                    ),
                    className="w-50 my-2",
                ),
                html.P(id="performance", className="mb-0"),
                html.P(id="allocation", className="mb-0"),
            ],
            className="d-flex flex-column align-items-center",
        ),
        html.Div(
            dcc.Graph(id="my-output", className="w-75"),
            className="d-flex justify-content-center w-100",
        ),
    ],
)


def calculate_allocation(df, weights, investment_amount):
    latest_prices = get_latest_prices(df)

    da = DiscreteAllocation(
        weights, latest_prices, total_portfolio_value=investment_amount
    )
    allocation, leftover = da.greedy_portfolio()
    return allocation, leftover


def calculate_optimal_portfolio(df):
    # Calculate expected returns and sample covariance
    mu = expected_returns.mean_historical_return(df)
    S = risk_models.sample_cov(df)

    # Optimize for maximal Sharpe ratio
    ef = EfficientFrontier(mu, S)
    raw_weights = ef.max_sharpe()
    cleaned_weights = ef.clean_weights()
    with Capturing() as performance:
        ef.portfolio_performance(verbose=True)

    return performance, cleaned_weights


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout


@app.callback(
    Output("my-output", "figure"),
    Output("performance", "children"),
    Output("allocation", "children"),
    Input("period", "value"),
    Input("investment-amount", "value"),
    Input("stocks", "value"),
    Input("calculate-btn", "n_clicks"),
)
@logger.catch
def update_output_div(period, investment_amount, selected_stocks, btn):
    if not selected_stocks:
        selected_stocks = [default_stock_choice]

    try:
        df = (
            yf.download(selected_stocks, period=period)[["Close"]]
            .droplevel(0, axis=1)
            .reset_index()
        )
    except ValueError:
        df = (
            yf.download(selected_stocks, period=period)[["Close"]]
            .reset_index()
            .rename(columns={"Close": selected_stocks[0]})
        )

    performance = ["Unable to optimize."]
    allocation = ""

    if selected_stocks.__len__() > 1:
        try:
            performance, cleaned_weights = calculate_optimal_portfolio(
                df.set_index("Date")
            )
            if performance.__len__() > 1:
                if investment_amount and "calculate-btn" == ctx.triggered_id:
                    allocation, leftover = calculate_allocation(
                        df.set_index("Date"), cleaned_weights, investment_amount
                    )
                    _ = []
                    for ticker, count in allocation.items():
                        _ += [f"{count} {ticker} stocks"]
                    allocation = "Your asset allocation: " + ", ".join(_)

                df["Optimal portfolio"] = (
                    df.iloc[:, 1:].assign(**cleaned_weights).mul(df).sum(1)
                )
        except OptimizationError:
            logger.info("Oops")

    df.iloc[:, 1:] = ((df.iloc[:, 1:].pct_change(1) + 1).cumprod() - 1).fillna(0)
    df = pd.melt(
        df,
        value_vars=df.columns[1:],
        var_name="Stock",
        id_vars="Date",
        value_name="Value",
    )

    fig = px.line(
        df,
        x="Date",
        y="Value",
        color="Stock",
        template="simple_white",
    )

    fig.add_hline(y=0, line_width=2, line_dash="dash", line_color="black")
    fig.update_traces(hovertemplate="%{y:.1%}")
    fig.update_layout(yaxis_tickformat=".0%")
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(showline=True, linewidth=2, linecolor="black")

    return fig, "\n".join(performance), allocation


if __name__ == "__main__":
    app.run_server(debug=True)
