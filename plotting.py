# -*- coding: utf-8 -*-
import plotly.graph_objs as go
import pandas as pd

def plot_trends(data, trend_days_list):
    trends = []
    for days in trend_days_list:
        trend_data = data['Close'].rolling(window=days, min_periods=1).mean()
        trends.append(go.Scatter(x=data.index, y=trend_data, mode='lines', name=f'{days}-Day MA'))
    return trends

def plot_bollinger_bands(data):
    rolling_mean = data['Close'].rolling(window=20).mean()
    rolling_std = data['Close'].rolling(window=20).std()
    upper_band = rolling_mean + (rolling_std * 2)
    lower_band = rolling_mean - (rolling_std * 2)
    upper_band = upper_band.dropna()
    lower_band = lower_band.dropna()
    upper_band_trace = go.Scatter(x=upper_band.index, y=upper_band, fill='tonexty', name='Upper Bollinger Band')
    lower_band_trace = go.Scatter(x=lower_band.index, y=lower_band, fill='tonexty', name='Lower Bollinger Band')
    return upper_band_trace, lower_band_trace

def plot_macd(data):
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    macd_trace = go.Scatter(x=data.index, y=macd, mode='lines', name='MACD')
    signal_trace = go.Scatter(x=data.index, y=signal, mode='lines', name='Signal')
    histogram_trace = go.Bar(
        x=data.index,
        y=histogram,
        name='Histogram',
        marker=dict(
            color=['green' if h >= 0 else 'red' for h in histogram],
            opacity=0.5
        )
    )
    return [macd_trace, signal_trace, histogram_trace]

def plot_breakout(data):
    if len(data) < 50:
        print(f"Debug: For faa data til breakout ({len(data)} raekker). Kraever mindst 50.")
        return go.Scatter(x=[], y=[], mode='markers', name='Breakout'), [], False

    # Beregn glidende gennemsnit og volumen-gennemsnit
    ma10 = data['Close'].rolling(window=10).mean()
    ma20 = data['Close'].rolling(window=20).mean()
    ma50 = data['Close'].rolling(window=50).mean()
    avg_volume = data['Volume'].rolling(window=20).mean()

    # Beregn MACD og Signal
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    # Tjek for NaN-værdier
    if any(pd.isna([ma10.iloc[-1], ma20.iloc[-1], ma50.iloc[-1], avg_volume.iloc[-1], macd.iloc[-1], signal.iloc[-1]])):
        print(f"Debug: NaN-vaerdier fundet i beregninger: MA10={ma10.iloc[-1]}, MA20={ma20.iloc[-1]}, "
              f"MA50={ma50.iloc[-1]}, AvgVol={avg_volume.iloc[-1]}, MACD={macd.iloc[-1]}, Signal={signal.iloc[-1]}")
        return go.Scatter(x=[], y=[], mode='markers', name='Breakout'), [], False

    print(f"Debug: MA10 (sidste 5): {ma10[-5:].to_dict()}")
    print(f"Debug: MA20 (sidste 5): {ma20[-5:].to_dict()}")
    print(f"Debug: MA50 (sidste 5): {ma50[-5:].to_dict()}")
    print(f"Debug: Gennemsnitlig volumen (sidste 5): {avg_volume[-5:].to_dict()}")
    print(f"Debug: MACD (sidste 5): {macd[-5:].to_dict()}")
    print(f"Debug: Signal (sidste 5): {signal[-5:].to_dict()}")

    breakout_points = []
    for i in range(50, len(data)):
        try:
            # Tjek MACD over Signal med lille tærskel
            is_macd_above_signal = macd.iloc[i] > signal.iloc[i] + 0.01
            # Tjek volumen-spike
            is_volume_spike = data['Volume'].iloc[i] > 1.1 * avg_volume.iloc[i]
            # Tjek MA-betingelser
            is_10ma_above_20ma = ma10.iloc[i] > ma20.iloc[i]
            is_10ma_upward = ma10.iloc[i] > ma10.iloc[i-1]
            is_20ma_upward = ma20.iloc[i] > ma20.iloc[i-1]
            is_close_above_50ma = data['Close'].iloc[i] > ma50.iloc[i]
            # Fjernet is_50ma_upward for at gøre betingelserne mindre strenge

            # Log betingelser for debugging
            if not is_macd_above_signal:
                print(f"Debug: MACD-betingelse fejlet ved index {i}: MACD={macd.iloc[i]}, Signal={signal.iloc[i]}")
            if not is_volume_spike:
                print(f"Debug: Volumen-betingelse fejlet ved index {i}: Volumen={data['Volume'].iloc[i]}, "
                      f"AvgVol={avg_volume.iloc[i]}, Taerskel={1.1 * avg_volume.iloc[i]}")
            if not is_10ma_above_20ma:
                print(f"Debug: 10MA > 20MA fejlet ved index {i}: MA10={ma10.iloc[i]}, MA20={ma20.iloc[i]}")
            if not is_close_above_50ma:
                print(f"Debug: Close > 50MA fejlet ved index {i}: Close={data['Close'].iloc[i]}, MA50={ma50.iloc[i]}")
            if not is_10ma_upward:
                print(f"Debug: 10MA opadgaaende fejlet ved index {i}: MA10={ma10.iloc[i]}, MA10_prev={ma10.iloc[i-1]}")
            if not is_20ma_upward:
                print(f"Debug: 20MA opadgaaende fejlet ved index {i}: MA20={ma20.iloc[i]}, MA20_prev={ma20.iloc[i-1]}")

            # Hvis alle betingelser er opfyldt, markér som breakout
            if (is_macd_above_signal and is_volume_spike and is_10ma_above_20ma and
                is_10ma_upward and is_20ma_upward and is_close_above_50ma):
                print(f"Debug: Breakout detekteret ved index {i}, dato {data.index[i]}: "
                      f"Close={data['Close'].iloc[i]}, MA10={ma10.iloc[i]}, MA20={ma20.iloc[i]}, "
                      f"MA50={ma50.iloc[i]}, Volumen={data['Volume'].iloc[i]}, AvgVol={avg_volume.iloc[i]}, "
                      f"MACD={macd.iloc[i]}, Signal={signal.iloc[i]}")
                breakout_points.append({
                    'x': data.index[i],
                    'y': data['Close'].iloc[i] * 0.95,  # Placer under grafen (5% under Close)
                    'close': data['Close'].iloc[i],
                    'text': 'Breakout'
                })
        except Exception as e:
            print(f"Debug: Fejl ved breakout-detektion for index {i}: {e}")
            continue

    breakout_trace = go.Scatter(
        x=[p['x'] for p in breakout_points],
        y=[p['y'] for p in breakout_points],
        mode='markers',
        name='Breakout',
        marker=dict(symbol='triangle-up', size=10, color='green'),
        text=[p['text'] for p in breakout_points],
        hovertemplate='Breakout<br>Date: %{x}<br>Price: %{customdata:.2f}<extra></extra>',
        customdata=[p['close'] for p in breakout_points]
    )

    annotations = [
        dict(
            x=p['x'],
            y=p['y'],
            xref="x",
            yref="y",
            text="Breakout",
            showarrow=False,
            font=dict(size=10, color='green'),
            yshift=-15  # Flyt tekst under trekant
        ) for p in breakout_points
    ]

    print(f"Debug: Breakout-trace genereret med {len(breakout_points)} punkter")
    return breakout_trace, annotations, len(breakout_points) > 0