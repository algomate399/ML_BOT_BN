import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, clone ,TransformerMixin
from arch.bootstrap import MovingBlockBootstrap


class BaggingBootstrapper(BaseEstimator , ClassifierMixin) :
    def __init__(self , estimator , n_estimators=5 , threshold=0.5 , sample_weight=None , random_state=None) :
        self.estimator=estimator
        self.threshold=threshold
        self.n_estimators=n_estimators
        self.sample_weight=sample_weight
        self.random_state=random_state
        self.fitted_models=[]
        self.strapper=None
        self.classes_=None
        self.n_classes_=None

    def fit(self , X , y) :
        self.classes_=np.unique(y)
        self.n_classes_=len(self.classes_)
        self.threshold_array=np.full(self.n_classes_ , self.threshold)
        block_size=X.shape[0] // self.n_estimators
        self.strapper=MovingBlockBootstrap(block_size , X , y , seed=self.random_state)
        self.fitted_models.clear()

        for sample in self.strapper.bootstrap(self.n_estimators) :
            X_train , y_train=sample[0][0] , sample[0][1]
            clone_estimator=clone(self.estimator)
            sample_weight=self.sample_weight[X_train.index] if self.sample_weight is not None else None
            clone_estimator.fit(X_train , y_train , sample_weight=sample_weight)
            self.fitted_models.append(clone_estimator)

        return self

    def predict_proba(self , X) :
        probabilities=np.array([model.predict_proba(X) for model in self.fitted_models])
        return np.mean(probabilities , axis=0)

    def predict(self , X) :
        proba=self.predict_proba(X)

        above_threshold=proba >= self.threshold_array
        predicted_indices=np.where(
            above_threshold.any(axis=1) ,
            np.argmax(proba * above_threshold , axis=1) ,
            np.argmax(proba , axis=1)
        )

        return self.classes_[predicted_indices]


class NoiseEnhancer(BaseEstimator , TransformerMixin) :
    def __init__(self , mu=0.0 , sigma=0.0 , skip_cols=[] , random_state=None) :
        self.mu=mu
        self.sigma=sigma
        self.skip_cols=skip_cols
        self.random_state=random_state

    def fit(self , x , y=None) :
        return self

    def fit_transform(self , X , y=None) :
        X=X.copy()
        col=[c for c in X.columns if c not in self.skip_cols]
        np.random.seed(self.random_state)
        noise=np.random.normal(self.mu , self.sigma , X[col].shape) if self.sigma else 0
        X[col]+=noise
        return X

    def transform(self , X , y=None) :
        return X


class VolatilityScaler(BaseEstimator , TransformerMixin) :
    def __init__(self , xi , c=3.0 , col_name='_VOL_RAW_REG_' , skip_cols=[] , transformer=False) :
        self.c=c
        self.transformer=transformer
        self.skip_cols=skip_cols
        self.col_name=col_name
        self.xi=self.transformer(xi) if self.transformer else xi
        self.col=None

    def fit(self , x , y=None) :
        self.col=[c for c in x.columns if c not in self.skip_cols+[self.col_name]]
        return self

    def transform(self , X) :
        X=X.copy()
        yi=self.transformer(X[self.col_name]) if self.transformer else X[self.col_name]

        sigma=(yi / self.xi).clip(upper=self.c)
        X[self.col]=X[self.col].div(sigma , axis=0)
        return X.drop(self.col_name , axis=1)


