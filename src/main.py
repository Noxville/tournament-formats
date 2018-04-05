from operator import methodcaller
from concurrent import futures
import threading

from formats import *
from utils import * 


formats = []
for perc in [0]:
	for to_win in [1,2,3]:
		for seeding in ['random', 'standard']:
			for size in [8, 16]:
				for form in [
						SingleElim(team_gen(size), perception_error=perc, seeding=seeding, to_win=to_win),
				]: formats.append(form)

	formats.append(GSLInto4TeamSingleElim(team_gen(8), 'Starladder iLeague Season 3 / 4 / 5', perception_error=perc))
	formats.append(GSLInto4TeamSingleElim(team_gen(8), 'PGL Open Bucharest', perception_error=perc, finals=2))
	formats.append(GSLInto4TeamSingleElim(team_gen(8), 'ESL One Hamburg', perception_error=perc, gsl_games=[1,2,2,2], finals=2))
	formats.append(EightTeamDoubleElim(team_gen(8), 'Dota Pit Season 6', perception_error=perc))
	# perfect world masters ~ 
	formats.append(EightTeamDoubleElim(team_gen(8), 'DreamLeague Season 8 / 9', perception_error=perc, lb=2))
	# dota summit ~ 9 team event
	formats.append(GSLInto8TeamSingleElim(team_gen(8), 'Captain\'s Draft 4.0', perception_error=perc, gsl_games=[1,1,1,1]))
	# esl one genting
	# esl one kato
	# bucharest major
	formats.append(GSLIntoBubble(team_gen(8), 'GESC Indonesia', perception_error=perc))
	# DAC
	# gesc thailand
	# MDL Changsha
	# ESL One birmingham
	# China supermajor

with futures.ThreadPoolExecutor(max_workers=16) as pool:
	output = pool.map(methodcaller('run'), formats)

	for e in sorted([(_[0].name, _[0].n, _[1].matrix_score()) for _ in output], key=lambda x: x[2]):
		print(e)
