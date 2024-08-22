# market_dash.py
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import yfinance as yf
import pandas as pd
import datetime as dt

app = dash.Dash(__name__)

# Scrape wiki for the tickers
sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
sp500_table = pd.read_html(sp500_url, header=0)
sp500_tickers = sp500_table[0]['Symbol'].tolist()

# Fetch S&P data
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

colors = {
    'background': '#f9f9f9',
    'text': '#333333',
    'primary': '#636EFA',
    'secondary': '#EF553B',
    'accent': '#00CC96',
    'light': '#D9D9D9'
}

app.layout = html.Div(style={'backgroundColor': colors['background'], 'padding': '20px'}, children=[
    html.H1("Market Dashboard", style={'textAlign': 'center', 'color': colors['text'], 'marginBottom': '30px'}),
    
    html.Div([
        dcc.Dropdown(
            id='stock-ticker',
            options=[{'label': ticker, 'value': ticker} for ticker in historical_data.keys()],
            value='AAPL',
            multi=False,
            style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'middle', 'borderRadius': '8px', 'borderColor': colors['light']}
        ),
        
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=min_date,
            end_date=max_date,
            display_format='YYYY-MM-DD',
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            initial_visible_month=max_date,
            style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'middle', 'borderRadius': '8px', 'borderColor': colors['light']}
        )
    ], style={'marginBottom': '30px'}),
    
    html.Div([
        html.Div([
            html.H3("Stock Metrics", style={'color': colors['primary'], 'marginBottom': '10px'}),
            html.Div(id='stock-metrics', style={'fontSize': '18px', 'fontWeight': 'bold', 'color': colors['text']})
        ], style={'backgroundColor': colors['light'], 'padding': '20px', 'borderRadius': '8px'}),
        
        html.Div([
            html.H3("S&P 500 Metrics", style={'color': colors['secondary'], 'marginBottom': '10px'}),
            html.Div(id='sp500-metrics', style={'fontSize': '18px', 'fontWeight': 'bold', 'color': colors['text']})
        ], style={'backgroundColor': colors['light'], 'padding': '20px', 'borderRadius': '8px'})
    ], style={'marginBottom': '30px'}),
    
    html.Div([
        dcc.Graph(id='stock-graph', animate=True, style={'backgroundColor': colors['background'], 'borderRadius': '8px'}),
        dcc.Graph(id='sp500-graph', animate=True, style={'backgroundColor': colors['background'], 'borderRadius': '8px'})
    ], style={'marginBottom': '30px'}),
    
    html.Div([
        dcc.Graph(id='moving-average-graph', animate=True, style={'backgroundColor': colors['background'], 'borderRadius': '8px'}),
        dcc.Graph(id='volume-graph', animate=True, style={'backgroundColor': colors['background'], 'borderRadius': '8px'})
    ])
])

@app.callback(
    [Output('stock-graph', 'figure'),
     Output('sp500-graph', 'figure'),
     Output('moving-average-graph', 'figure'),
     Output('volume-graph', 'figure'),
     Output('stock-metrics', 'children'),
     Output('sp500-metrics', 'children')],
    [Input('stock-ticker', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_graphs(selected_ticker, start_date, end_date):
    try:
        df = historical_data[selected_ticker]
        filtered_df = df.loc[start_date:end_date]
        if filtered_df.empty:
            raise ValueError("No data available for the specified time range.")
        
        stock_current_price = filtered_df['Close'][-1]
        stock_change = (stock_current_price - filtered_df['Close'][0]) / filtered_df['Close'][0] * 100
        
        sp500_filtered_df = sp500_data.loc[start_date:end_date]
        sp500_current_price = sp500_filtered_df['Close'][-1]
        sp500_change = (sp500_current_price - sp500_filtered_df['Close'][0]) / sp500_filtered_df['Close'][0] * 100
        
        stock_graph = go.Figure(
            data=[go.Scatter(x=filtered_df.index, y=filtered_df['Close'], mode='lines', name=selected_ticker, line=dict(color=colors['primary']))],
            layout=go.Layout(
                title=f'{selected_ticker} Historical Price',
                xaxis_title='Time',
                yaxis_title='Price',
                xaxis=dict(range=[filtered_df.index.min(), filtered_df.index.max()]),
                yaxis=dict(range=[filtered_df['Close'].min(), filtered_df['Close'].max()]),
                paper_bgcolor=colors['background'],
                plot_bgcolor=colors['background'],
                font=dict(color=colors['text'])
            )
        )
        
        # S&P 500 graph
        sp500_graph = go.Figure(
            data=[go.Scatter(x=sp500_filtered_df.index, y=sp500_filtered_df['Close'], mode='lines', name='S&P 500', line=dict(color=colors['secondary']))],
            layout=go.Layout(
                title='S&P 500 Historical Price',
                xaxis_title='Time',
                yaxis_title='Price',
                xaxis=dict(range=[sp500_filtered_df.index.min(), sp500_filtered_df.index.max()]),
                yaxis=dict(range=[sp500_filtered_df['Close'].min(), sp500_filtered_df['Close'].max()]),
                paper_bgcolor=colors['background'],
                plot_bgcolor=colors['background'],
                font=dict(color=colors['text'])
            )
        )
        
        # Moving average graph
        moving_avg = filtered_df['Close'].rolling(window=20).mean()
        moving_average_graph = go.Figure(
            data=[go.Scatter(x=filtered_df.index, y=moving_avg, mode='lines', name='20-Day Moving Average', line=dict(color=colors['accent']))],
            layout=go.Layout(
                title=f'{selected_ticker} 20-Day Moving Average',
                xaxis_title='Time',
                yaxis_title='Moving Average',
                xaxis=dict(range=[filtered_df.index.min(), filtered_df.index.max()]),
                yaxis=dict(range=[moving_avg.min(), moving_avg.max()]),
                paper_bgcolor=colors['background'],
                plot_bgcolor=colors['background'],
                font=dict(color=colors['text'])
            )
        )
        
        # Volume graph
        volume_graph = go.Figure(
            data=[go.Bar(x=filtered_df.index, y=filtered_df['Volume'], name='Volume', marker_color=colors['primary'])],
            layout=go.Layout(
                title=f'{selected_ticker} Trading Volume',
                xaxis_title='Time',
                yaxis_title='Volume',
                xaxis=dict(range=[filtered_df.index.min(), filtered_df.index.max()]),
                yaxis=dict(range=[filtered_df['Volume'].min(), filtered_df['Volume'].max()]),
                paper_bgcolor=colors['background'],
                plot_bgcolor=colors['background'],
                font=dict(color=colors['text'])
            )
        )
        
        # Metrics
        stock_metrics = [
            html.P(f"Current Price: ${stock_current_price:.2f}", style={'margin': '0'}),
            html.P(f"Change: {stock_change:.2f}%", style={'margin': '0'})
        ]
        
        sp500_metrics = [
            html.P(f"Current Price: ${sp500_current_price:.2f}", style={'margin': '0'}),
            html.P(f"Change: {sp500_change:.2f}%", style={'margin': '0'})
        ]
        
        return stock_graph, sp500_graph, moving_average_graph, volume_graph, stock_metrics, sp500_metrics

    except Exception as e:
        empty_graph = go.Figure(
            data=[go.Scatter(x=[], y=[], mode='lines', name=selected_ticker)],
            layout=go.Layout(
                title=f'{selected_ticker} - Data Unavailable',
                xaxis_title='Time',
                yaxis_title='Price',
                annotations=[dict(text=str(e), showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)],
                paper_bgcolor=colors['background'],
                plot_bgcolor=colors['background'],
                font=dict(color=colors['text'])
            )
        )
        
        return empty_graph, empty_graph, empty_graph, empty_graph, [html.P("Error fetching stock data.")], [html.P("Error fetching S&P 500 data.")]

if __name__ == '__main__':
    app.run_server(debug=True)
