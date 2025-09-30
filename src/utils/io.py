import os
import pandas as pd
from pathlib import Path
from src.data.generate import generate_datasets

DATA_DIR = Path("data")


def ensure_data_ready(force_refresh: bool = False):
	DATA_DIR.mkdir(exist_ok=True)
	users_fp = DATA_DIR / "users.csv"
	events_fp = DATA_DIR / "events.csv"
	need = force_refresh or (not users_fp.exists()) or (not events_fp.exists())
	if not need and events_fp.exists():
		try:
			df = pd.read_csv(events_fp, parse_dates=["event_time"]) 
			latest = df["event_time"].max().normalize()
			if latest < pd.Timestamp.today().normalize():
				need = True
		except Exception:
			need = True
	if need:
		users, events = generate_datasets()
		users.to_csv(users_fp, index=False)
		events.to_csv(events_fp, index=False)


def load_datasets():
	users = pd.read_csv(DATA_DIR / "users.csv")
	events = pd.read_csv(DATA_DIR / "events.csv", parse_dates=["event_time"])
	return users, events


def regenerate_datasets():
	users, events = generate_datasets()
	(users, events)
	users.to_csv(DATA_DIR / "users.csv", index=False)
	events.to_csv(DATA_DIR / "events.csv", index=False)
	return users, events
