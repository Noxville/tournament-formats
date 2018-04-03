from formats import *
from utils import * 


formats = []
for perc in [25]:
	for to_win in [2,3]:
		for seeding in ['standard']:
			for size in [8, 16]:
				for form in [
						SingleElim(team_gen(size), perception_error=perc, seeding=seeding, to_win=to_win),
				]: formats.append(form)


for f in formats:
	r = f.run()
	print(f.name)
	print(r.summary())
