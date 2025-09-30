import pandas as pd
import plotly.express as px


def build_cohorts(events: pd.DataFrame, cohort_event: str = "signup", outcome_event: str = "purchase", period: str = "weekly") -> pd.DataFrame:
	# Map each user to first cohort_event time and its period bucket
	events = events.copy()
	cohort_src = events[events["event_name"] == cohort_event][["user_id", "event_time"]].sort_values("event_time").drop_duplicates("user_id")
	period_freq = "W" if period == "weekly" else "M"
	cohort_src["cohort_period"] = cohort_src["event_time"].dt.to_period(period_freq)

	# Outcomes joined to cohort and compute period offset
	outcomes = events[events["event_name"] == outcome_event][["user_id", "event_time"]].copy()
	if outcomes.empty or cohort_src.empty:
		return pd.DataFrame()
	outcomes = outcomes.merge(cohort_src[["user_id", "event_time", "cohort_period"]].rename(columns={"event_time": "cohort_time"}), on="user_id", how="inner")
	outcomes["out_period"] = outcomes["event_time"].dt.to_period(period_freq)
	outcomes["period_index"] = (outcomes["out_period"] - outcomes["cohort_period"]).apply(lambda x: x.n)
	outcomes = outcomes[outcomes["period_index"] >= 0]

	# Cohort sizes
	cohort_sizes = cohort_src.groupby("cohort_period")["user_id"].nunique().rename("size").reset_index()

	# Unique converting users per cohort by period index
	ret = outcomes.groupby(["cohort_period", "period_index"])['user_id'].nunique().reset_index()
	ret = ret.merge(cohort_sizes, on="cohort_period", how="left")
	ret["retention"] = ret["user_id"] / ret["size"].replace(0, 1)

	pivot = ret.pivot(index="cohort_period", columns="period_index", values="retention").fillna(0.0)
	# Make JSON-serializable labels
	pivot.index = pivot.index.astype(str)
	pivot.columns = pivot.columns.astype(int)
	return pivot


def plot_retention(pivot: pd.DataFrame):
	if pivot is None or pivot.empty:
		return px.imshow([[0.0]], labels=dict(color="Retention"), title="No data for selected filters")
	fig = px.imshow(pivot, color_continuous_scale="Blues", aspect="auto", origin="lower", labels=dict(color="Retention"))
	fig.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
	return fig
