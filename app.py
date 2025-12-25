from dash import Dash, dcc, html, Input, Output, State, ctx
import plotly.graph_objs as go
from data import cached_get_stock_data, get_pe_ratio, get_beta, load_tickers, save_tickers, load_preferences, save_preferences, normalize_ticker, get_company_name, add_ticker_to_list, delete_ticker_from_list
from plotting import plot_trends, plot_bollinger_bands, plot_macd, plot_breakout
#import dash
import numpy as np
import pandas as pd

def create_app():
    app = Dash(__name__)

    # Initialiser præferencer
    preferences = load_preferences()
    valid_trend_days = [5, 10, 20, 50, 100, 200]
    tickers = load_tickers()

    print(f"Debug: Præferencer ved opstart: {preferences}")

    app.layout = html.Div([
        html.H1("Stock Analysis"),
        dcc.Store(id='theme-store'),
        dcc.Store(id='init-store', data={'load': True}),  # Trigger til sideload
        html.Script('''
            function updateTheme() {
                var theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                document.getElementById('theme-store').value = theme;
                var event = new Event('input');
                document.getElementById('theme-store').dispatchEvent(event);
                console.log('Debug: Tema opdateret til: ' + theme);
            }
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateTheme);
            updateTheme();
        '''),
        html.Script('''
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(function() {
                    ['stock-graph', 'volume-graph', 'macd-graph'].forEach(function(graphId) {
                        var graph = document.querySelector('#' + graphId + ' .plotly');
                        if (graph) {
                            console.log('Debug: ' + graphId + ' container bredde: ' + graph.offsetWidth + 'px');
                        } else {
                            console.log('Debug: ' + graphId + ' ikke fundet i DOM');
                        }
                    });
                }, 1000);
            });
        '''),
        html.Div([
            html.Div([
                html.Label("Select Ticker", style={'font-weight': 'bold'}),
                html.Div([
                    html.Div(
                        dcc.Dropdown(
                            id='ticker-dropdown',
                            options=[{'label': f'{ticker} - {long_name}', 'value': ticker} for ticker, long_name in tickers.items()],
                            value=None,  # Initial værdi sættes via callback
                            style={'width': '100%'}
                        ),
                        style={'flex-grow': '1'},
                        title="Choose a stock ticker from the dropdown list"
                    ),
                    html.Button('Slet', id='delete-ticker-button', n_clicks=0, style={'margin-left': '5px', 'background-color': '#ff4d4d', 'color': 'white', 'border': 'none', 'padding': '0 15px', 'cursor': 'pointer', 'border-radius': '3px', 'height': '36px'}),
                ], style={'display': 'flex', 'align-items': 'center'}),
                dcc.ConfirmDialog(id='confirm-delete', message='Er du sikker på, at du vil slette denne aktie fra listen?'),
            ], style={'width': '50%', 'display': 'inline-block', 'padding': '5px'}),
            html.Div([
                html.Label("Add New Ticker", style={'font-weight': 'bold'}),
                html.Div(
                    dcc.Input(id='new-ticker-input', type='text', placeholder='Add new ticker', debounce=True),
                    title="Enter a new stock ticker here"
                ),
                html.Button('Add Ticker', id='add-ticker-button', n_clicks=0, title="Click to add the entered ticker"),
            ], style={'padding': '10px', 'width': '100%'}),
            html.Div([
                html.Label("Select Time Span", style={'font-weight': 'bold'}),
                html.Div(
                    dcc.Dropdown(
                        id='timespan-dropdown',
                        options=[
                            {'label': '1 Day', 'value': '1d'},
                            {'label': '1 Week', 'value': '1w'},
                            {'label': '1 Month', 'value': '1mo'},
                            {'label': '3 Months', 'value': '3mo'},
                            {'label': '6 Months', 'value': '6mo'},
                            {'label': '1 Year', 'value': '1y'},
                            {'label': '3 Years', 'value': '3y'},
                            {'label': '5 Years', 'value': '5y'},
                            {'label': '10 Years', 'value': '10y'},
                            {'label': 'Max', 'value': 'max'}
                        ],
                        value=preferences["timespan"],
                        style={'width': '100%'}
                    ),
                    title="Choose the time period for the stock data"
                )
            ], style={'width': '25%', 'display': 'inline-block', 'padding': '5px'}),
        ], style={'display': 'flex', 'justify-content': 'space-between'}),
        html.Div(
            dcc.Checklist(
                id='trend-checkbox',
                options=[{'label': f'{x} Days Trend', 'value': x} for x in valid_trend_days],
                value=preferences["trend_days"],
                labelStyle={'display': 'inline-block'}
            ),
            title="Toggle to display trend lines for the stock data"
        ),
        html.Div(
            dcc.Checklist(
                id='bollinger-checkbox',
                options=[{'label': 'Show Bollinger Bands', 'value': 'bollinger'}],
                value=['bollinger'] if preferences.get("bollinger") else [],
                labelStyle={'display': 'inline-block'}
            ),
            title="Toggle to display Bollinger Bands for the stock chart"
        ),
        html.Div(
            dcc.Checklist(
                id='legend-checkbox',
                options=[{'label': 'Show all legends', 'value': 'show_legends'}],
                value=['show_legends'] if preferences.get("show_legends") else [],
                labelStyle={'display': 'inline-block'}
            ),
            title="Toggle to display all legends on the graph"
        ),
        html.Div(
            dcc.Checklist(
                id='candlestick-checkbox',
                options=[{'label': 'Show Candlestick', 'value': 'candlestick'}],
                value=['candlestick'] if preferences.get("candlestick") else [],
                labelStyle={'display': 'inline-block'}
            ),
            title="Toggle to display candlestick chart"
        ),
        html.Div([dcc.Graph(id='stock-graph', config={'responsive': True}, style={'width': '100%', 'min-height': '400px'})], style={'width': '100%'}),
        html.Div([dcc.Graph(id='volume-graph', config={'responsive': True}, style={'width': '100%', 'min-height': '400px'})], style={'width': '100%'}),
        html.Div([dcc.Graph(id='macd-graph', config={'responsive': True}, style={'width': '100%', 'min-height': '400px'})], style={'width': '100%'})
    ])

    @app.callback(
        Output('ticker-dropdown', 'value'),
        Input('init-store', 'data'),
        prevent_initial_call=False
    )
    def initialize_ticker(data):
        preferences = load_preferences()
        tickers = load_tickers()
        last_ticker = preferences.get("last_ticker")
        if not last_ticker or last_ticker not in tickers:
            last_ticker = next(iter(tickers), "TSLA")
            print(f"Debug: last_ticker fra præferencer ugyldig eller mangler ({preferences.get('last_ticker')}). Bruger fallback: {last_ticker}")
        else:
            print(f"Debug: Hentet last_ticker fra præferencer ved sideload: {last_ticker}")

        if last_ticker not in tickers:
            print(f"Debug: last_ticker {last_ticker} ikke i tickers. Tilføjer til tickers.json.")
            company_name = get_company_name(last_ticker)
            tickers[last_ticker] = company_name
            save_tickers(tickers)

        print(f"Debug: Initialiserer ticker-dropdown med last_ticker: {last_ticker}")
        return last_ticker

    @app.callback(
        Output('stock-graph', 'figure'),
        [
            Input('ticker-dropdown', 'value'),
            Input('timespan-dropdown', 'value'),
            Input('trend-checkbox', 'value'),
            Input('bollinger-checkbox', 'value'),
            Input('legend-checkbox', 'value'),
            Input('candlestick-checkbox', 'value'),
            Input('theme-store', 'data')
        ]
    )
    def update_graph(ticker, timespan, trend_days_list, bollinger_option, legend_toggle, candlestick_option, theme):
        print(f"Debug: update_graph kaldt med ticker: {ticker}, timespan: {timespan}, trend_days: {trend_days_list}, tema: {theme}")
        if not ticker:
            print("Debug: Ingen ticker valgt i update_graph. Returnerer tom graf.")
            return {
                'data': [],
                'layout': go.Layout(title='No Ticker Selected')
            }

        # Valider trend_days_list
        valid_trend_days = [5, 10, 20, 50, 100, 200]
        trend_days_list = [int(day) for day in trend_days_list if str(day).isdigit() and int(day) in valid_trend_days]
        if not trend_days_list:
            trend_days_list = valid_trend_days
            print(f"Debug: trend_days_list tom eller ugyldig. Bruger standard: {trend_days_list}")

        # Opdater præferencer
        preferences = load_preferences()
        updated_preferences = {
            "trend_days": trend_days_list,
            "bollinger": 'bollinger' in bollinger_option,
            "timespan": timespan,
            "show_legends": 'show_legends' in legend_toggle,
            "candlestick": 'candlestick' in candlestick_option,
            "last_ticker": normalize_ticker(ticker),
            "language": preferences.get("language", "en")
        }
        print(f"Debug: Opdaterer præferencer i update_graph for ticker {ticker}: {updated_preferences}")
        save_preferences(updated_preferences)

        data, ticker_long = cached_get_stock_data(ticker, timespan)

        if data.empty or 'Close' not in data:
            print(f"Debug: Kunne ikke hente eller behandle data for {ticker_long} i update_graph.")
            return {
                'data': [],
                'layout': go.Layout(title=f'Kunne ikke hente data for {ticker_long}')
            }

        traces = []

        if 'candlestick' in candlestick_option:
            traces.append(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name=f'{ticker_long} Close'
            ))
        else:
            initial_price = data['Close'].iloc[0]
            data['percent_change'] = ((data['Close'] - initial_price) / initial_price) * 100
            traces.append(go.Scatter(
                x=data.index,
                y=data['Close'],
                mode='lines',
                name=f'{ticker_long} Close',
                text=data['percent_change'].apply(lambda x: f'{x:.2f}%'),
                hoverinfo='text+x+y'
            ))

        trends = plot_trends(data, trend_days_list)
        traces.extend(trends)

        if 'bollinger' in bollinger_option:
            upper_band, lower_band = plot_bollinger_bands(data)
            traces.extend([upper_band, lower_band])

        use_breakout = preferences.get('use_breakout', False)
        if use_breakout:
            breakout_trace, breakout_annotations, has_breakout = plot_breakout(data)
            traces.append(breakout_trace)
        else:
            has_breakout = False
            breakout_annotations = []

        # Tilføj handels-signaler (køb/sælg) som markører på grafen
        try:
            if 'signal' in data:
                sig = data['signal']
                # find steder hvor signal ændrer sig
                changes = sig[sig != sig.shift(1)]
                buys = changes[changes == 1]
                sells = changes[changes == -1]

                shapes = []
                extra_annotations = []

                if not buys.empty:
                    buy_trace = go.Scatter(
                        x=buys.index,
                        y=data.loc[buys.index, 'Close'],
                        mode='markers',
                        name='Buy Signal',
                        marker=dict(symbol='triangle-up', size=12, color='green'),
                        hovertemplate='Buy<br>Date: %{x}<br>Price: %{y:,.2f}<extra></extra>'
                    )
                    traces.append(buy_trace)

                    # Add vertical lines and arrow annotation for buys
                    for d in buys.index:
                        shapes.append({
                            'type': 'line',
                            'xref': 'x', 'x0': d, 'x1': d,
                            'yref': 'paper', 'y0': 0, 'y1': 1,
                            'line': {'color': 'green', 'width': 2, 'dash': 'dot'}
                        })
                        extra_annotations.append({
                            'x': d, 'xref': 'x', 'y': 0.98, 'yref': 'paper',
                            'text': '▲', 'showarrow': False,
                            'font': {'size': 14, 'color': 'green'}
                        })

                if not sells.empty:
                    sell_trace = go.Scatter(
                        x=sells.index,
                        y=data.loc[sells.index, 'Close'],
                        mode='markers',
                        name='Sell Signal',
                        marker=dict(symbol='triangle-down', size=12, color='red'),
                        hovertemplate='Sell<br>Date: %{x}<br>Price: %{y:,.2f}<extra></extra>'
                    )
                    traces.append(sell_trace)

                    # Add vertical lines and arrow annotation for sells
                    for d in sells.index:
                        shapes.append({
                            'type': 'line',
                            'xref': 'x', 'x0': d, 'x1': d,
                            'yref': 'paper', 'y0': 0, 'y1': 1,
                            'line': {'color': 'red', 'width': 2, 'dash': 'dot'}
                        })
                        extra_annotations.append({
                            'x': d, 'xref': 'x', 'y': 0.02, 'yref': 'paper',
                            'text': '▼', 'showarrow': False,
                            'font': {'size': 14, 'color': 'red'}
                        })

                # Merge shapes/annotations into breakout_annotations (used in layout)
                try:
                    if isinstance(breakout_annotations, list):
                        breakout_annotations.extend(extra_annotations)
                    else:
                        breakout_annotations = extra_annotations
                except Exception:
                    breakout_annotations = extra_annotations

                # Save shapes to data for later inclusion in layout
                data['_signal_shapes'] = shapes

                # Print besked ved ny ændring i sidste række
                try:
                    last_row = data.iloc[-1]
                    prev_row = data.iloc[-2]
                    if int(last_row['signal']) == 1 and int(prev_row['signal']) != 1:
                        print(f"🚀 NYT KØB: Trenden er nu i Perfect Order for {ticker_long}!")
                    elif int(last_row['signal']) == -1 and int(prev_row['signal']) != -1:
                        print(f"⚠️ SÆLG/ADVARSEL: Trenden er brudt for {ticker_long}.")
                except Exception:
                    pass
        except Exception as e:
            print(f"Debug: Fejl ved tilføjelse af trade-signaler til grafen: {e}")

        pe_ratio = get_pe_ratio(ticker)
        beta = get_beta(ticker)

        title = f'{ticker_long} Stock Analysis'
        if has_breakout:
            title += ' | Breakout Detected'
        if pe_ratio:
            title += f' | PE: {pe_ratio:.2f}'
        if beta is not None:
            title += f' | Beta: {beta:.2f}'

        x_range = [data.index.min(), data.index.max()]
        bg_color = 'white' if theme == 'light' else 'rgb(30,30,30)'
        font_color = 'black' if theme == 'light' else 'white'

        figure = {
            'data': traces,
            'layout': go.Layout(
                title=title,
                xaxis={
                    'rangeslider': {'visible': False},
                    'showgrid': True,
                    'fixedrange': True,
                    'range': x_range
                },
                yaxis={'title': 'Price'},
                showlegend='show_legends' in legend_toggle,
                legend=dict(
                    orientation='v',
                    yanchor='top',
                    y=1,
                    xanchor='left',
                    x=0,
                    bgcolor='rgba(255,255,255,0.5)'
                ),
                annotations=breakout_annotations,
                shapes=(data.pop('_signal_shapes') if '_signal_shapes' in data else []),
                paper_bgcolor=bg_color,
                plot_bgcolor=bg_color,
                font=dict(color=font_color),
                margin=dict(l=60, r=40, t=40, b=40),
                autosize=True
            )
        }

        print(f"Debug: Stock-graf genereret succesfuldt for {ticker_long}, autosize=True, tema: {theme}")
        return figure

    @app.callback(
        Output('macd-graph', 'figure'),
        [
            Input('ticker-dropdown', 'value'),
            Input('timespan-dropdown', 'value'),
            Input('legend-checkbox', 'value'),
            Input('theme-store', 'data')
        ]
    )
    def update_macd_graph(ticker, timespan, legend_toggle, theme):
        print(f"Debug: update_macd_graph kaldt med ticker: {ticker}, timespan: {timespan}, tema: {theme}")
        if not ticker:
            print("Debug: Ingen ticker valgt i update_macd_graph. Returnerer tom graf.")
            return {'data': [], 'layout': go.Layout(title='No Ticker Selected for MACD')}

        data, ticker_long = cached_get_stock_data(ticker, timespan)

        if data.empty or 'Close' not in data:
            print(f"Debug: Kunne ikke hente eller behandle data for {ticker_long} i update_macd_graph.")
            return {
                'data': [],
                'layout': go.Layout(title=f'Kunne ikke hente data for {ticker_long} MACD')
            }

        try:
            macd_traces = plot_macd(data)
        except Exception as e:
            print(f"Debug: Fejl ved generering af MACD-graf for {ticker_long}: {e}")
            return {
                'data': [],
                'layout': go.Layout(title=f'Fejl ved generering af MACD-graf for {ticker_long}')
            }

        x_range = [data.index.min(), data.index.max()]
        bg_color = 'white' if theme == 'light' else 'rgb(30,30,30)'
        font_color = 'black' if theme == 'light' else 'white'

        macd_figure = {
            'data': macd_traces,
            'layout': go.Layout(
                title=f'{ticker_long} MACD',
                xaxis={
                    'rangeslider': {'visible': False},
                    'showgrid': True,
                    'matches': 'x',
                    'range': x_range
                },
                yaxis={'title': 'MACD'},
                showlegend='show_legends' in legend_toggle,
                legend=dict(
                    x=0,
                    y=1,
                    xanchor='left',
                    yanchor='top',
                    bgcolor='rgba(255,255,255,0.5)'
                ),
                paper_bgcolor=bg_color,
                plot_bgcolor=bg_color,
                font=dict(color=font_color),
                margin=dict(l=60, r=40, t=40, b=40),
                autosize=True
            )
        }

        print(f"Debug: MACD-graf genereret succesfuldt for {ticker_long}, autosize=True, tema: {theme}")
        return macd_figure

    @app.callback(
        Output('volume-graph', 'figure'),
        [
            Input('ticker-dropdown', 'value'),
            Input('timespan-dropdown', 'value'),
            Input('legend-checkbox', 'value'),
            Input('theme-store', 'data')
        ]
    )
    def update_volume_graph(ticker, timespan, legend_toggle, theme):
        print(f"Debug: update_volume_graph kaldt med ticker: {ticker}, timespan: {timespan}, tema: {theme}")
        if not ticker:
            print("Debug: Ingen ticker valgt i update_volume_graph. Returnerer tom graf.")
            return {
                'data': [],
                'layout': go.Layout(title='No Ticker Selected for Volume')
            }

        data, ticker_long = cached_get_stock_data(ticker, timespan)

        if data.empty or 'Volume' not in data or 'Close' not in data:
            print(f"Debug: Kunne ikke hente eller behandle data for {ticker_long} i update_volume_graph.")
            return {
                'data': [],
                'layout': go.Layout(title=f'Kunne ikke hente data for {ticker_long} Volume')
            }

        try:
            # Valider volumen-data
            volume_data = data['Volume'].dropna()
            # Tillad nul-værdier i volumen (nogle tickers/intervals bruger 0 ved ingen aktivitet).
            # Afvis kun, hvis der findes negative værdier eller datasættet er tomt.
            if volume_data.empty or (volume_data < 0).any():
                print(f"Debug: Ugyldige volumen-data for {ticker_long}: Tomt eller negative værdier")
                return {
                    'data': [],
                    'layout': go.Layout(title=f'Ugyldige volumen-data for {ticker_long}')
                }

            # Tjek for NaN eller manglende værdier
            if data['Volume'].isna().any() or data['Close'].isna().any():
                print(f"Debug: NaN-værdier fundet i volumen- eller Close-data for {ticker_long}. Fjerner NaN.")
                data = data.dropna(subset=['Volume', 'Close'])

            # Sørg for, at vi har nok data
            if len(data) < 1:
                print(f"Debug: Utilstrækkelige data for {ticker_long}: Mindst 1 datapunkt kræves")
                return {
                    'data': [],
                    'layout': go.Layout(title=f'Utilstrækkelige data for {ticker_long} Volume')
                }

            # Log data for at tjekke rækkevidde og værdier
            mid_point = len(data) // 2
            print(f"Debug: Volumen-data for {ticker_long}: Startdato={data.index.min()}, Slutdato={data.index.max()}, Længde={len(data)}")
            print(f"Debug: Volumen-værdier: Min={data['Volume'].min()}, Max={data['Volume'].max()}")
            print(f"Debug: Volumen-data før midtpunkt: {data['Volume'].iloc[:mid_point].tail(5).to_dict()}")
            print(f"Debug: Volumen-data efter midtpunkt: {data['Volume'].iloc[mid_point:].head(5).to_dict()}")

            # Beregn farver for alle datapunkter
            volume_colors = ['green']  # Første punkt får standardfarve
            for i in range(1, len(data)):
                color = 'green' if data['Close'].iloc[i] > data['Close'].iloc[i-1] else 'red'
                volume_colors.append(color)

            # Tegn nul-volumen som en meget lille epsilon (usynlig effekt på skala),
            # men behold original værdi i hover via `customdata`. Sæt lav opacity for nul.
            original_vol = data['Volume'].copy()
            max_vol = original_vol.max() if original_vol.max() > 0 else 1
            eps = max(1, int(max_vol * 1e-6))
            plot_vol = original_vol.copy()
            plot_vol[plot_vol == 0] = eps

            # Lav per-bar opacity: lavere for oprindelige 0-værdier
            opacities = [0.35 if v == 0 else 1.0 for v in original_vol]

            # Opret volumen-trace med alle datapunkter, brug customdata til hover
            volume_trace = go.Bar(
                x=data.index,
                y=plot_vol,
                name='Volume',
                marker=dict(color=volume_colors, opacity=opacities),
                customdata=original_vol,
                hovertemplate='Date: %{x}<br>Volume: %{customdata:,.0f}<extra></extra>'
            )
        except Exception as e:
            print(f"Debug: Fejl ved generering af volume-graf for {ticker_long}: {e}")
            return {
                'data': [],
                'layout': go.Layout(title=f'Fejl ved generering af volume-graf for {ticker_long}')
            }

        x_range = [data.index.min(), data.index.max()]
        bg_color = 'white' if theme == 'light' else 'rgb(30,30,30)'
        font_color = 'black' if theme == 'light' else 'white'

        volume_figure = {
            'data': [volume_trace],
            'layout': go.Layout(
                title=f'{ticker_long} Volume',
                xaxis={
                    'rangeslider': {'visible': False},
                    'showgrid': True,
                    'matches': 'x',
                    'range': x_range,
                    'tickfont': {'size': 10}
                },
                yaxis={
                    'title': 'Volume',
                    'rangemode': 'tozero',
                    'autorange': True,
                    'zeroline': True,
                    'tickformat': ',.0f',
                    'showgrid': True
                },
                # Bevar brugerens zoom/axis state på opdateringer for at undgå
                # at grafikalen skifter og skjuler små eller nul-højder.
                uirevision='volume-graph',
                showlegend='show_legends' in legend_toggle,
                legend=dict(
                    x=0,
                    y=1,
                    xanchor='left',
                    yanchor='top',
                    bgcolor='rgba(255,255,255,0.5)'
                ),
                paper_bgcolor=bg_color,
                plot_bgcolor=bg_color,
                font=dict(color=font_color),
                margin=dict(l=60, r=40, t=40, b=40),
                autosize=True
            )
        }

        # Hvis vi har genereret signal-shapes tidligere, inkluder dem i hoved-figurens layout
        try:
            shapes = []
            if '_signal_shapes' in data:
                shapes = data.pop('_signal_shapes')
            if shapes:
                # Inkluder shapes i både volume_figure og hoved-figure via global scope
                volume_figure['layout']['shapes'] = shapes
        except Exception:
            pass

        print(f"Debug: Volume-graf genereret succesfuldt for {ticker_long}, autosize=True, tema: {theme}")
        return volume_figure

    @app.callback(
        Output('confirm-delete', 'displayed'),
        Input('delete-ticker-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def display_confirm_delete(n_clicks):
        if n_clicks:
            return True
        return False

    @app.callback(
        [Output('ticker-dropdown', 'options'), Output('ticker-dropdown', 'value', allow_duplicate=True)],
        [Input('add-ticker-button', 'n_clicks'), Input('confirm-delete', 'submit_n_clicks')],
        [State('new-ticker-input', 'value'), State('ticker-dropdown', 'value')],
        prevent_initial_call=True
    )
    def manage_tickers(add_clicks, delete_clicks, new_ticker, current_ticker):
        trigger = ctx.triggered_id
        print(f"Debug: manage_tickers kaldt af {trigger}")

        if trigger == 'add-ticker-button' and new_ticker:
            success, message = add_ticker_to_list(new_ticker)
            if success:
                print(f"Debug: Succes - {message}")
                current_ticker = normalize_ticker(new_ticker)
                # Opdater præferencer
                preferences = load_preferences()
                preferences["last_ticker"] = current_ticker
                save_preferences(preferences)
            else:
                print(f"Debug: Fejl ved tilføjelse - {message}")

        elif trigger == 'confirm-delete' and current_ticker:
            success, message = delete_ticker_from_list(current_ticker)
            if success:
                print(f"Debug: Slettet - {message}")
                # Vælg en ny ticker (den første i listen) eller None hvis listen er tom
                tickers = load_tickers()
                current_ticker = next(iter(tickers)) if tickers else None

                preferences = load_preferences()
                preferences["last_ticker"] = current_ticker if current_ticker else "TSLA"
                save_preferences(preferences)

        tickers = load_tickers()
        options = [{'label': f'{ticker} - {long_name}', 'value': ticker} for ticker, long_name in tickers.items()]
        return options, current_ticker

    @app.callback(
        Output('ticker-dropdown', 'value', allow_duplicate=True),
        Input('ticker-dropdown', 'value'),
        prevent_initial_call=True
    )
    def update_ticker_preference(ticker):
        print(f"Debug: Callback aktiveret i update_ticker_preference med ticker: {ticker}")
        if ticker:
            preferences = load_preferences()
            normalized_ticker = normalize_ticker(ticker)
            preferences["last_ticker"] = normalized_ticker
            print(f"Debug: Gemmer præferencer i update_ticker_preference: {preferences}")
            save_preferences(preferences)
        else:
            print("Debug: Ingen ticker valgt i update_ticker_preference. Sætter til standard TSLA.")
            preferences = load_preferences()
            preferences["last_ticker"] = "TSLA"
            save_preferences(preferences)
            ticker = "TSLA"
        print(f"Debug: Returnerer ticker til dropdown: {ticker}")
        return ticker

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)