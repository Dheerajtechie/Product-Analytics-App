import pandas as pd
import plotly.graph_objects as go


def build_funnel(events: pd.DataFrame, steps: list[str], window: pd.Timedelta) -> pd.DataFrame:
	# Consider users who hit the first step, then compute stepwise completion
	if not steps:
		return pd.DataFrame(columns=["step", "users"])
	first = steps[0]
	first_hits = events[events["event_name"] == first][["user_id", "event_time"]].rename(columns={"event_time": "t0"})
	funnel = []
	eligible = first_hits.copy()
	for idx, step in enumerate(steps):
		if idx == 0:
			funnel.append({"step": step, "users": eligible["user_id"].nunique()})
			continue
		eh = events[events["event_name"] == step][["user_id", "event_time"]]
		joined = eligible.merge(eh, on="user_id")
		joined = joined[(joined["event_time"] >= joined["t0"]) & (joined["event_time"] <= joined["t0"] + window)]
		completed_users = joined.groupby("user_id")["event_time"].min().reset_index().rename(columns={"event_time": f"t{idx}"})
		eligible = eligible.merge(completed_users, on="user_id", how="inner")
		funnel.append({"step": step, "users": eligible["user_id"].nunique()})
	return pd.DataFrame(funnel)


def plot_funnel(funnel_df: pd.DataFrame):
	fig = go.Figure(go.Funnel(y=funnel_df["step"], x=funnel_df["users"]))
	fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
	return fig
