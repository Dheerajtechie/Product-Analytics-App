import pandas as pd
import numpy as np
import plotly.express as px


def compute_daily_metrics(events: pd.DataFrame) -> pd.DataFrame:
	frame = events.copy()
	frame["date"] = frame["event_time"].dt.date
	daily_users = frame.groupby("date")["user_id"].nunique().rename("dau").reset_index()
	purchasers = frame[frame["event_name"] == "purchase"].groupby("date")["user_id"].nunique().rename("purchasers").reset_index()
	signups = frame[frame["event_name"] == "signup"].groupby("date")["user_id"].nunique().rename("signups").reset_index()
	metrics = daily_users.merge(signups, on="date", how="left").merge(purchasers, on="date", how="left").fillna(0)
	metrics["conversion"] = metrics.apply(lambda r: (r["purchasers"] / r["signups"]) if r["signups"] > 0 else 0.0, axis=1)
	metrics = metrics.sort_values("date")
	return metrics


def detect_anomalies(series: pd.Series, window: int = 14, z_thresh: float = 3.0) -> pd.DataFrame:
	df = pd.DataFrame({"value": series}).copy()
	df["mean"] = df["value"].rolling(window=window, min_periods=max(3, window//2)).mean()
	df["std"] = df["value"].rolling(window=window, min_periods=max(3, window//2)).std().replace(0, np.nan)
	df["z"] = (df["value"] - df["mean"]) / df["std"]
	df["is_anom"] = df["z"].abs() >= z_thresh
	return df


def plot_metric_with_anomalies(dates: pd.Series, values: pd.Series, title: str, anomalies: pd.Series) -> "px.Figure":
	df = pd.DataFrame({"date": pd.to_datetime(dates), "value": values, "anomaly": anomalies})
	fig = px.line(df, x="date", y="value", title=title)
	points = df[df["anomaly"]]
	if not points.empty:
		fig.add_scatter(x=points["date"], y=points["value"], mode="markers", name="Anomaly", marker=dict(color="red", size=10))
	fig.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10))
	return fig
