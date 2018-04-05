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

def gsl(ts, gsl_games):	
	(opening_games, winners_games, losers_games, decider_games) = gsl_games
	
	g1 = boX(ts[0], ts[3], opening_games)
	g2 = boX(ts[1], ts[2], opening_games)
	winners = boX(g1[0], g2[0], winners_games)
	losers = boX(g1[1], g2[1], losers_games)
	decider = boX(winners[1], losers[0], decider_games)

	return [winners[0], decider[0], decider[1], losers[1]]