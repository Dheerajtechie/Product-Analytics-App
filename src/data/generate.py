import numpy as np
import pandas as pd
from numpy.random import default_rng
import datetime as dt

rng = default_rng(42)


def generate_users(num_users: int = 50000, start: str | pd.Timestamp | None = None, end: str | pd.Timestamp | None = None) -> pd.DataFrame:
	# Default to rolling last 180 days ending today
	if end is None:
		end_dt = pd.Timestamp.today().normalize()
	else:
		end_dt = pd.Timestamp(end)
	if start is None:
		start_dt = end_dt - pd.Timedelta(days=180)
	else:
		start_dt = pd.Timestamp(start)

	# Sample signup times uniformly over the window
	start_s = int(start_dt.timestamp())
	end_s = int((end_dt + pd.Timedelta(days=1)).timestamp())  # inclusive end day
	join_dates = pd.to_datetime(rng.integers(start_s, end_s, size=num_users), unit="s")
	channels = rng.choice(["organic", "paid", "referral", "seo"], size=num_users, p=[0.45, 0.35, 0.10, 0.10])
	country = rng.choice(["US", "IN", "BR", "DE", "GB", "CA"], size=num_users, p=[0.35, 0.25, 0.15, 0.10, 0.10, 0.05])
	return pd.DataFrame({
		"user_id": np.arange(1, num_users + 1),
		"signup_time": join_dates.sort_values().values,
		"acq_channel": channels,
		"country": country,
	})


def simulate_events(users: pd.DataFrame, end: pd.Timestamp | None = None) -> pd.DataFrame:
	if end is None:
		end = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
	events = []
	for _, u in users.iterrows():
		# view probability by channel/country
		base_view = 0.6 if u["acq_channel"] in ("organic", "seo") else 0.5
		base_view *= 1.1 if u["country"] in ("US", "DE", "GB") else 0.9
		signup_time = pd.to_datetime(u["signup_time"]).tz_localize(None)
		if signup_time >= end:
			continue
		if rng.random() < base_view:
			pre_time = signup_time - pd.Timedelta(hours=int(rng.integers(1, 72)))
			if pre_time < end:
				events.append((u.user_id, "view", pre_time))

		activate_prob = 0.55 if u["acq_channel"] != "paid" else 0.45
		activate_prob *= 1.1 if u["country"] in ("US", "DE", "GB") else 0.95
		if rng.random() < activate_prob:
			activate_time = signup_time + pd.Timedelta(days=int(abs(rng.normal(1.5, 2))))
			if activate_time < end:
				events.append((u.user_id, "activate", activate_time))
				purchase_prob = 0.28 if u["acq_channel"] in ("organic", "referral") else 0.22
				purchase_prob *= 1.15 if u["country"] in ("US", "GB") else 0.9
				if rng.random() < purchase_prob:
					purchase_time = activate_time + pd.Timedelta(days=int(abs(rng.normal(3.0, 4))))
					if purchase_time < end:
						events.append((u.user_id, "purchase", purchase_time))

		# engagement events across weeks
		n_days = int(rng.integers(1, 30))
		for _ in range(n_days):
			if rng.random() < base_view * 0.7:
				delta = pd.Timedelta(days=int(abs(rng.normal(7, 10))))
				eng_time = signup_time + delta
				if eng_time < end:
					events.append((u.user_id, "view", eng_time))

	# add explicit signup events
	for _, u in users.iterrows():
		st = pd.to_datetime(u["signup_time"]).tz_localize(None)
		if st < end:
			events.append((u.user_id, "signup", st))

	events_df = pd.DataFrame(events, columns=["user_id", "event_name", "event_time"]).sort_values("event_time").reset_index(drop=True)
	return events_df


def generate_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
	end_dt = pd.Timestamp.today().normalize()
	users = generate_users(end=end_dt)
	events = simulate_events(users, end=end_dt + pd.Timedelta(days=1))
	return users, events
