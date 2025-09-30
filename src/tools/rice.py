import pandas as pd


def score_rice(df: pd.DataFrame) -> pd.DataFrame:
	req_cols = ["Item", "Reach", "Impact", "Confidence", "Effort"]
	for c in req_cols:
		if c not in df.columns:
			raise ValueError(f"Missing column: {c}")
	result = df.copy()
	result["RICE"] = (result["Reach"] * result["Impact"] * result["Confidence"]) / result["Effort"].replace(0, 1e-9)
	return result
