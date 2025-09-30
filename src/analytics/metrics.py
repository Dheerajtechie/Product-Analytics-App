import pandas as pd


def compute_kpis(users: pd.DataFrame, events: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> dict:
	frame = events[(events["event_time"] >= start) & (events["event_time"] < end)].copy()
	frame["date"] = frame["event_time"].dt.date

	# Active users
	daily_active = frame.groupby("date")["user_id"].nunique()
	wau = frame.copy()
	wau["week"] = wau["event_time"].dt.isocalendar().week
	weekly_active = wau.groupby("week")["user_id"].nunique()
	mau = frame.copy()
	mau["month"] = mau["event_time"].dt.to_period("M")
	monthly_active = mau.groupby("month")["user_id"].nunique()

	# Conversion (signup -> purchase within window)
	signups = frame[frame["event_name"] == "signup"]["user_id"].unique()
	purchasers = frame[frame["event_name"] == "purchase"]["user_id"].unique()
	conversion = 0.0 if len(signups) == 0 else len(set(purchasers) & set(signups)) / len(signups)

	# Simple retention snapshot: next-week activity after signup
	signup_events = events[events["event_name"] == "signup"].copy()
	signup_events["week"] = signup_events["event_time"].dt.isocalendar().week
	future = events.copy()
	future["week"] = future["event_time"].dt.isocalendar().week
	ret = (
		future.merge(signup_events[["user_id", "week"]], on="user_id", suffixes=("", "_signup"))
		.assign(retained=lambda d: (d["week"] >= d["week_signup"] + 1) & (d["week"] <= d["week_signup"] + 4))
		.groupby("week_signup")["retained"].mean().reset_index().rename(columns={"week_signup": "cohort_week", "retained": "retention"})
	)

	return {
		"dau_avg": float(daily_active.mean()) if not daily_active.empty else 0.0,
		"wau_avg": float(weekly_active.mean()) if not weekly_active.empty else 0.0,
		"mau_avg": float(monthly_active.mean()) if not monthly_active.empty else 0.0,
		"conversion_rate": float(conversion),
		"retention": ret,
	}
