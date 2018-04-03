class Team:
    def __init__(self, true_skill, rank):
        self.true_skill = true_skill
        self.rank = rank
        self.perceived_skill = true_skill
    
    def __repr__(self):
    	return "{} ({}) ~~ {:06.1f}".format(self.true_skill, self.rank, self.perceived_skill)
        