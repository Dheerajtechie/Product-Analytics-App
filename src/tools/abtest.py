import math
import numpy as np


def _z(p: float) -> float:
	# Approximate normal quantile function
	if p <= 0.5:
		return -_z(1 - p)
	
	# Simple approximation for common values
	if p >= 0.95:
		return 1.96
	elif p >= 0.90:
		return 1.645
	elif p >= 0.80:
		return 1.28
	elif p >= 0.70:
		return 1.04
	else:
		return 0.84


def ab_sample_size(p1: float, p2: float, alpha: float = 0.05, power: float = 0.8) -> int:
	# Two-proportion z-test sample size per group
	z_alpha = _z(alpha)
	z_beta = _z(power)
	p_bar = (p1 + p2) / 2
	se = math.sqrt(2 * p_bar * (1 - p_bar))
	delta = abs(p2 - p1)
	n = 2 * (z_alpha * se + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (delta ** 2)
	return int(math.ceil(n / 2))


def ab_detectable_effect(baseline: float, n_per_group: int, alpha: float = 0.05, power: float = 0.8) -> float:
	z_alpha = _z(alpha)
	z_beta = _z(power)
	p = baseline
	se = math.sqrt(2 * p * (1 - p))
	delta = (z_alpha * se + z_beta * math.sqrt(2 * p * (1 - p))) / math.sqrt(n_per_group)
	return max(1e-6, delta)
