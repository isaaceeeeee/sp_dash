# market_dash.py

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import yfinance as yf
import pandas as pd
import datetime as dt

app = dash.Dash(__name__)

# Scrape wiki for tickers 
sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
sp500_table = pd.read_html(sp500_url, header=0)
sp500_tickers = sp500_table[0]['Symbol'].tolist()
# Collect Data from yahoo
sp500_data = yf.download('^GSPC', period="max")

# DATA
historical_data = {}
min_date = pd.Timestamp.max
for ticker in sp500_tickers:
    try:
        df = yf.download(ticker, period="max")
        if not df.empty:
            historical_data[ticker] = df
            min_date = min(min_date, df.index.min())  
    except Exception as e:
        print(f"Skipping ticker {ticker}: {e}")

max_date = dt.datetime.now()

# APP LAYOUT
app.layout = html.Div([
    html.H1("Market Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        dcc.Dropdown(
            id='stock-ticker',
            options=[{'label': ticker, 'value': ticker} for ticker in historical_data.keys()],
            value='AAPL',
            multi=False,
            style={'width': '48%', 'display': 'inline-block'}
        ),
        
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=min_date,
            end_date=max_date,
            display_format='YYYY-MM-DD',
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            initial_visible_month=max_date,
            style={'width': '48%', 'display': 'inline-block'}
        )
    ], style={'padding': '20px'}),
    
    html.Div([
        html.Div([
            html.H3("Stock Metrics"),
            html.Div(id='stock-metrics', style={'fontSize': 18, 'fontWeight': 'bold'})
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            html.H3("S&P 500 Metrics"),
            html.Div(id='sp500-metrics', style={'fontSize': 18, 'fontWeight': 'bold'})
        ], style={'width': '48%', 'display': 'inline-block'})
    ], style={'padding': '20px'}),
    
    dcc.Graph(id='historical-graph', animate=True)
])

@app.callback(
    [Output('historical-graph', 'figure'),
     Output('stock-metrics', 'children'),
     Output('sp500-metrics', 'children')],
    [Input('stock-ticker', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_graph(selected_ticker, start_date, end_date):
    try:
        # Stock data
        df = historical_data[selected_ticker]
        filtered_df = df.loc[start_date:end_date]
        if filtered_df.empty:
            raise ValueError("No data available for the specified time range.")
        
        stock_current_price = filtered_df['Close'][-1]
        stock_change = (stock_current_price - filtered_df['Close'][0]) / filtered_df['Close'][0] * 100
        
        # S&P 500 data
        sp500_filtered_df = sp500_data.loc[start_date:end_date]
        sp500_current_price = sp500_filtered_df['Close'][-1]
        sp500_change = (sp500_current_price - sp500_filtered_df['Close'][0]) / sp500_filtered_df['Close'][0] * 100
        
        # Create figures
        figure = go.Figure(
            data=[
                go.Scatter(x=filtered_df.index, y=filtered_df['Close'], mode='lines', name=selected_ticker),
                go.Scatter(x=sp500_filtered_df.index, y=sp500_filtered_df['Close'], mode='lines', name='S&P 500', line=dict(dash='dash'))
            ],
            layout=go.Layout(
                title=f'{selected_ticker} vs S&P 500',
                xaxis_title='Time',
                yaxis_title='Price',
                xaxis=dict(range=[filtered_df.index.min(), filtered_df.index.max()]),
                yaxis=dict(range=[min(filtered_df['Close'].min(), sp500_filtered_df['Close'].min()), max(filtered_df['Close'].max(), sp500_filtered_df['Close'].max())])
            )
        )
        
        # Metrics
        stock_metrics = [
            html.P(f"Current Price: ${stock_current_price:.2f}"),
            html.P(f"Change: {stock_change:.2f}%")
        ]
        
        sp500_metrics = [
            html.P(f"Current Price: ${sp500_current_price:.2f}"),
            html.P(f"Change: {sp500_change:.2f}%")
        ]
        
        return figure, stock_metrics, sp500_metrics

    except Exception as e:
        figure = go.Figure(
            data=[go.Scatter(x=[], y=[], mode='lines', name=selected_ticker)],
            layout=go.Layout(
                title=f'{selected_ticker} - Data Unavailable',
                xaxis_title='Time',
                yaxis_title='Price',
                annotations=[dict(text=str(e), showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)]
            )
        )
        
        return figure, [html.P("Error fetching stock data.")], [html.P("Error fetching S&P 500 data.")]

if __name__ == '__main__':
    app.run_server(debug=True)
