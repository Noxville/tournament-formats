from math import log
from random import random
from models import Team

def team_gen(n, start=1200, step=25):
	return [Team(_, 1 + i) for i, _ in enumerate(range(1200, 1200 - (step * n), -1 * step))]


def boX(ta, tb, towin=2):
    a, b = 0, 0
    d = (0.0 + ta.true_skill - tb.true_skill) / 400.0
    odds = 1. / (1. + pow(10.0, d))

    while a != towin and b != towin:
        if random() > odds:
            a += 1
        else:
            b += 1
    return [ta, tb] if a > b else [tb, ta]

def sePairings(n):
	rds = round(log(n , 2)) - 1
	order = [1, 2]
	for i in range(rds):
		order = seLayer(order)
	return [_-1 for _ in order]

def seLayer(l):
	layer = []
	length = 1 + (2 * len(l))
	for _ in l:
		layer.append(_)
		layer.append(length - _)
	return layer

def stripPlace(st):
	return int(st.split("-")[0])

def chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]

def gsl(ts, gsl_games):	
	(opening_games, winners_games, losers_games, decider_games) = gsl_games
	
	g1 = boX(ts[0], ts[3], opening_games)
	g2 = boX(ts[1], ts[2], opening_games)
	winners = boX(g1[0], g2[0], winners_games)
	losers = boX(g1[1], g2[1], losers_games)
	decider = boX(winners[1], losers[0], decider_games)

	return [winners[0], decider[0], decider[1], losers[1]]

class RRRes:
	def __init__(self, team, wins=0, losses=0, tiebreakers=0, series_wins=0, series_draws=0, series_losses=0):
		self.team = team
		self.wins = wins
		self.losses = losses
		self.tiebreakers = tiebreakers
		self.series_wins = series_wins
		self.series_draws = series_draws
		self.series_losses = series_losses

	def score(self):
		return (1000 * self.wins) + self.tiebreakers

	def three_score(self):
		return (10000 * (3 * self.series_wins + self.series_draws)) + (100 * self.wins) + self.tiebreakers

	def __repr__(self):
		return "Team #{}: \t{}-{} raw\t+{} ={} -{} in series (tb: {}) ~~ raw score: {}\t\t, 3-pt score: {}".format(self.team.rank, self.wins, self.losses, self.series_wins, self.series_draws, self.series_losses, self.tiebreakers, self.score(), self.three_score())

def rr_fixed_games(ts, num_series=1, num_matches_per_series=1):
	""" 
		Round robin stuff where each matchup has a fixed number of games
	"""
	rmap = {}
	for t in ts:
		rmap[t] = RRRes(t)

	for a in ts:
			for b in ts:
				if (a.rank > b.rank): # ensure match(a, b) only happens once per cycle
					for ser in range(num_series):
						_gw = {}
						_gw[a] = 0
						_gw[b] = 0
						for n in range(num_matches_per_series):
							m = boX(a, b, 1)
							rmap[m[0]].wins += 1
							rmap[m[1]].losses += 1
							_gw[m[0]] = 1 + _gw[m[0]]

						if _gw[a] == _gw[b]:
							rmap[a].series_draws += 1
							rmap[b].series_draws += 1
						elif _gw[a] > _gw[b]:
							rmap[a].series_wins += 1
							rmap[b].series_losses += 1
						else:
							rmap[b].series_wins += 1
							rmap[a].series_losses += 1
	return rmap

def rr_box_matches(ts, box_wins_per_match=2):
	""" 
		Round robin stuff where each matchup is a boX
	"""
	for a in ts:
		for b in ts:
			if (a.rank > b.rank):
				m = boX(a, b, box_wins_per_match)

	# @todo: fix