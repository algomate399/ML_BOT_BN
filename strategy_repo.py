import pandas as pd
from datetime import datetime,timedelta
import numpy as np
import pandas_ta as ta
import pickle as pk
from sklearn.decomposition import PCA
from hmmlearn import hmm
from OrderParam import get_ensemble_n , get_params
import os

def Z_score(dt ,length):
    mean = dt.ewm(span=length).mean()
    std = dt.ewm(span=length).std()
    return (dt-mean)/std

def calculate_MOM_Burst( dt,lookback):
    candle_range = dt['high']-dt['low']
    mean_range = candle_range.rolling(window=lookback).mean()
    std_range = candle_range.rolling(window=lookback).std()
    mom_burst = (candle_range-mean_range)/std_range
    return mom_burst,mean_range

def line_angle(df_, n):
    angle = np.full_like(df_, np.nan)  # Initialize with NaNs

    for i in range(n, len(df_)):
        dist = i - (i - n)
        if dist != 0:
            angle[i] = np.arctan((df_.iloc[i] - df_.iloc[i - n]) / dist) * 180 / np.pi

    return pd.Series(angle, index=df_.index)

class STRATEGY_REPO:
    LIVE_FEED = None
    TICKER = None
    time_zone = None

    def __init__(self,name,symbol,Components, interval):
        self.strategy_name = name
        self.symbol = symbol
        self.Components = Components
        self.position = 0
        self.normalized_features = None
        self.data = None
        self.params = None
        self.STR_MTM = 0
        self.interval = interval
        self.model_1 = None
        self.pca_1 = None
        self.regime_model_1 = None
        self.ensemble_model = None
        self.model_type = 'long'
        self.base_ml = [None]
        self.pca_model = [None]
        self.load_model()


    def load_model(self):
        ensemble = get_ensemble_n(self.strategy_name)
        for n in range(1,ensemble+1):
            self.base_ml.append(self.get_model(n, 'ML'))
            self.pca_model.append(self.get_model(n, 'PCA'))

        self.regime_model_1 = self.get_model(1, 'REGIME')
        self.ensemble_model = self.get_model(1,'ENSEM')

    def get_model(self, n, model):
        file_name = f'{self.strategy_name}_{n}' if model == 'ML' else f'{self.strategy_name}_{model}_{n}'
        file_path = file_path = os.path.join('TRAINED_ML', self.strategy_name, self.model_type, f'{file_name}.pkl')
        with open(file_path, 'rb') as file:
            loaded_model = pk.load(file)
        return loaded_model

    def get_signal(self):
        feature = None
        self.data = self.TICKER.get_data(self.symbol, f'{self.interval}')
        # generating probabilities from base models
        for i, param in enumerate(get_params(self.strategy_name), start=1):
            self.generate_features(param)
            proba = self.get_prediction(i)
            if type(feature) == type(None):
                feature = proba
            else:
                feature = np.concatenate((feature, proba), axis=1)

        return self.ensemble_model.predict(feature)[-1]

    def get_prediction(self, n):
        model_input = self.pca_model[n].transform(self.normalized_features.values[-1].reshape(1, -1))
        return self.base_ml[n].predict_proba(model_input)

    def Normalization(self, features, normal_window=10, normalization=True):
        if normalization:
            features = features.dropna(axis=0)
            mean_val = features.rolling(window=normal_window).mean()
            std_val = features.rolling(window=normal_window).std()
            standardized_features = (features - mean_val) / (std_val + 1e-8)
        else:
            standardized_features = features

        return standardized_features.dropna(axis=0)

    def VolatilityRegime(self, vol_period=10):

        log_return = np.log(self.data['close'] / self.data['close'].shift(1))
        volatility = log_return.ewm(span=vol_period).std()

        features = pd.DataFrame()
        features['volatility'] = volatility * 100
        features['Range'] = 100 * (self.data['high'] - self.data['low']) / self.data['low']
        features['Range_prev_low'] = 100 * (self.data['high'] - self.data['low'].shift(1)) / self.data['low'].shift(1)

        return features

    def generate_features(self, params):

        if self.strategy_name == 'TREND_EMA':
            self.normalized_features, regime_input = self.TREND_EMA(**params)
        elif self.strategy_name == 'SharpeRev':
            self.normalized_features, regime_input = self.SharpeRev(**params)
        elif self.strategy_name == 'Volatility_BRK':
            self.normalized_features, regime_input = self.Volatility_BRK(**params)

        if self.strategy_name == 'TREND_EMA':
            for name in self.Components:
                dt = self.TICKER.get_data(name, f'{self.interval}')
                cmp_params = {'window': params['window'], 'normal_window': params['normal_window'],
                              'lags': params['lags'], 'id_': name}
                normalized_features_cmp = self.TREND_EMA_components(dt, **cmp_params)
                idx = self.normalized_features.index
                self.normalized_features = pd.concat([self.normalized_features, normalized_features_cmp.loc[idx]],
                                                     axis=1)

        # setting regimes
        regime = self.Regimer(regime_input)
        self.normalized_features = pd.concat([self.normalized_features, regime], axis=1)

    def TREND_EMA(self, window, lookback_1,lookback_2, normal_window, lags):

        # Initialization of variables
        features = pd.DataFrame()

#       calculating indicator values
        candle_range = self.data['high'] - self.data['low']
        rsi = ta.rsi(self.data['close'], window)
        EMA = self.data['close'].ewm(span=window).mean()
        angle_1 = line_angle(EMA, lookback_1)
        angle_2 = line_angle(EMA, lookback_2)
        zscore = Z_score(EMA, window)

#       calculating strategy components
        features['pct_change'] = self.data['close'].pct_change()
        features['rsi'] = rsi
        features['EMA'] = EMA
        features['spr'] = self.data['close'] / EMA
        features['candle_range'] = candle_range
        features['angle_1'] = angle_1
        features['angle_2'] = angle_2
        features['angle_ratio'] = angle_1 / angle_2
        features['zscore'] = zscore

#       calculating lagged features
        if lags:
            lag_values = pd.DataFrame()
            for col in features.columns:
                for lag in range(1, lags + 1):
                    lag_values[f'{col}_{lag}'] = features[col].shift(lag)
#       concatenate the feature and lag features
            features = pd.concat([features, lag_values], axis=1)

#       normalization the features
        normalized_features = self.Normalization(features, normal_window, True)
        normalized_features['dayofweek'] = normalized_features.index.dayofweek
        VolatilityRegime = self.VolatilityRegime()
        return normalized_features, VolatilityRegime.loc[normalized_features.index]

    def TREND_EMA_components(self,dt,window, normal_window, lags,id_):
        features = pd.DataFrame()

        # calculating the indicator values
        rsi = ta.rsi(dt['close'], window)
        EMA = dt['close'].ewm(span=window).mean()
        zscore = Z_score(dt['close'], window)

        # setting features
        features['rsi'] = rsi
        features['EMA'] = EMA
        features['zscore'] = zscore
        features['pct_change'] = dt['close'].pct_change()
        features['spr'] = dt['close'] / EMA

        if dt['volume'].mean() > 0:
            # volume based indicators
            average_volume = dt['volume'].rolling(window=window).mean()
            volume_score = (dt['volume'] - average_volume) / average_volume
            vwap = ta.vwap(dt['high'], dt['low'], dt['close'], dt['volume'])
            zscore_volume = Z_score(dt['volume'], window)

        #   setting volume based features
            features['vwap'] = vwap
            features['volume_score'] = volume_score
            features['volume_zscore'] = zscore_volume

        # calculating lagged features
        if lags:
            lag_values = pd.DataFrame()
            for col in features.columns:
                for lag in range(1, lags + 1):
                    lag_values[f'{col}_{lag}'] = features[col].shift(lag)
                    #       concatenate the feature and lag features
            features = pd.concat([features, lag_values], axis=1)

        # normalization the features
        normalized_features = self.Normalization(features, normal_window, True)
        normalized_features.columns = [f"{col}_{id_}" for col in normalized_features.columns]
        return normalized_features

    def SharpeRev(self,lookback, q_dn,q_up, window, normal_window, lags):
        # Initialization of variables
        features = pd.DataFrame()

        # calculating indicator values
        mean = self.data['close'].pct_change().rolling(window=lookback).mean() * 100
        std = self.data['close'].pct_change().rolling(window=lookback).std() * 100
        pct_change = self.data['close'].pct_change() * 100
        spr = (pct_change - mean) / std
        EMA = self.data['close'].ewm(span=lookback).mean()

        # calculating strategy components(spr , quantiles)
        features['spr'] = spr
        features['quan_up'] = features['spr'].rolling(window=window).quantile(q_up)
        features['quan_dn'] = features['spr'].rolling(window=window).quantile(q_dn)
        features['spr_quan_up'] = features['quan_up'] - features['spr']
        features['spr_quan_dn'] = features['spr'] - features['quan_dn']
        features['sentiment'] = EMA - self.data['close']
        features['pct_change'] = pct_change

        # adding lagged features
        if lags:
            lag_values = pd.DataFrame()
            for col in features.columns:
                for lag in range(1, lags + 1):
                    lag_values[f'{col}_{lag}'] = features[col].shift(lag)
        #   concatenate the feature and lag features
            features = pd.concat([features, lag_values], axis=1)

        # normalization the features
        normalized_features = self.Normalization(features, normal_window, True)
        normalized_features['dayofweek'] = normalized_features.index.dayofweek
        VolatilityRegime = self.VolatilityRegime()

        return normalized_features, VolatilityRegime.loc[normalized_features.index]

    def Volatility_BRK(self, lookback, band_width, normal_window, lags):
        #  initialization the variables
        features = pd.DataFrame()

        # calculating indicators
        variation_range = (self.data['high'] - self.data['low']).shift(1)
        mean_price = self.data['close'].rolling(window=lookback).mean()
        mean_range = variation_range.rolling(window=lookback).mean()
        volatility_band_UP = self.data['open'] + (band_width * mean_range)
        volatility_band_DN = self.data['open'] - (band_width * mean_range)
        cross_up_ratio = self.data['close'] - volatility_band_UP
        cross_dn_ratio = volatility_band_DN - self.data['close']
        band_ratio = volatility_band_UP - volatility_band_DN
        mean_vs_UP_BAND_score = volatility_band_UP - mean_price
        mean_vs_DN_BAND_score = mean_price - volatility_band_DN
        atr = ta.atr(self.data['high'], self.data['low'], self.data['close'], lookback)
        avg_vs_price = self.data['close'] - mean_price

        # setting features
        features['UP_BAND'] = volatility_band_UP
        features['DN_BAND'] = volatility_band_DN
        features['cross_up_ratio'] = cross_up_ratio
        features['cross_dn_ratio'] = cross_dn_ratio
        features['band_ratio'] = band_ratio
        features['mean_vs_band_UP'] = mean_vs_UP_BAND_score
        features['mean_vs_band_dn'] = mean_vs_DN_BAND_score
        features['mean_vs_close'] = avg_vs_price
        features['atr'] = atr
        features['pct_change'] = self.data['close'].pct_change()
        features['range_'] = variation_range

        #  calculating lagged features
        if lags:
            lag_values = pd.DataFrame()
            for col in features.columns:
                for lag in range(1, lags + 1):
                    lag_values[f'{col}_{lag}'] = features[col].shift(lag)
                    #       concatenate the feature and lag features
            features = pd.concat([features, lag_values], axis=1)

        #  normalization the features
        normalized_features = self.Normalization(features, normal_window, True)
        normalized_features['dayofweek'] = normalized_features.index.dayofweek
        # volatility Regime
        VolatilityRegime = self.VolatilityRegime()
        return normalized_features, VolatilityRegime.loc[normalized_features.index]

    def Regimer(self ,regime_input):
        # Volatility Regime
        states = pd.Series(self.regime_model_1.predict(regime_input),index= regime_input.index , name = 'Regime')
        return states










