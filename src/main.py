from operator import methodcaller
from multiprocessing import Pool
import threading

from formats import *
from utils import * 


formats = []
for perc in [0, 50]:
	for to_win in [1,2]:
		for seeding in ['random', 'standard']:
			for size in [8, 16]:
				for form in [
						SingleElim(team_gen(size), perception_error=perc, seeding=seeding, to_win=to_win),
				]: formats.append(form)

	formats.append(TheInternational2017(team_gen(18), 'The International 2017', perception_error=perc))
	formats.append(Perfect(team_gen(8), 'Perfect 8-team Format', perception_error=perc))
	formats.append(Worst(team_gen(8), 'Worst 8-team Format', perception_error=perc))
	formats.append(GSLInto4TeamSingleElim(team_gen(8), 'Starladder iLeague Season 3 / 4 / 5', perception_error=perc))
	formats.append(GSLInto4TeamSingleElim(team_gen(8), 'PGL Open Bucharest', perception_error=perc, finals=2))
	formats.append(GSLInto4TeamSingleElim(team_gen(8), 'ESL One Hamburg', perception_error=perc, gsl_games=[1,2,2,2], finals=2))
	formats.append(EightTeamDoubleElim(team_gen(8), 'Dota Pit Season 6', perception_error=perc))
	formats.append(PerfectWorldMasters(team_gen(10), 'Perfect World Masters', perception_error=perc))
	formats.append(EightTeamDoubleElim(team_gen(8), 'DreamLeague Season 8 / 9', perception_error=perc, lb=2))
	formats.append(SummitIdioticFormat(team_gen(9), 'Summit 8', perception_error=perc))
	formats.append(GSLInto8TeamSingleElim(team_gen(8), 'Captain\'s Draft 4.0', perception_error=perc, gsl_games=[1,1,1,1]))
	formats.append(ESLDoubleElimIntoSingleElim(team_gen(16), 'ESL Genting', perception_error=perc, playoff_game=False))
	formats.append(ESLDoubleElimIntoSingleElim(team_gen(16), 'ESL Katowice', perception_error=perc, playoff_game=True))
	formats.append(PGLBucharest(team_gen(16), 'PGL Bucharest Major', perception_error=perc))
	formats.append(GSLIntoBubble(team_gen(8), 'GESC Indonesia', perception_error=perc))
	formats.append(DotaAsiaChampionships(team_gen(16), 'Dota Asia Championships 2018', perception_error=perc))
	formats.append(MDLChangsha(team_gen(12), 'MDL Changsha', perception_error=perc))
	formats.append(Epicenter(team_gen(12), 'Epicenter', perception_error=perc))
	# gesc thailand
	formats.append(ESLTwelveTeamFormat(team_gen(12), 'ESL Birmingham', perception_error=perc, gsl_games=[1,2,2,2]))
	# China supermajor


print("Starting parallel evaluation")
with Pool() as pool:
	output = pool.map(methodcaller('run'), formats)

	for e in sorted([(_[0].name, _[0].n, _[0].perception_error, _[1].matrix_score(), _[1].top4()) for _ in output], key=lambda x: x[3]):
		print(e)
