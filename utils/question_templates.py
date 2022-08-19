
# Predicate is key. Value is a tuple with first one to find the subj and the second one to find the obj.
# n is the number of items that we are looking for.
# pred: (find_subj, find_obj)
question_templates = {'AtLocation': ('What can you see around {obj}? Name {n}.', 'Where is the {subj} located?? Name {n}.'), # TODO: Find Subject
                      'CapableOf': ('What thing {obj}? Name {n}.', 'What is {subj} capable of? Name {n}.'), # TODO: Find Subject
                      'Causes': ('What causes {obj}? Name {n}.', 'What {subj} can cause? Name {n}.'), # TODO: Both
                      'CausesDesire': ('What causes desire in {obj}? Name {n}.', 'What {subj} causes desire in? Name {n}'), # TODO: Both
                      'CreatedBy': ('Who creates {obj}? Name {n}.', 'What is created by {subj}? Name {n}.'), # TODO: Both
                      'DefinedAs': ('What word means {obj}? Name {n}.','What is the definition of {subj}? Name {n}.'), # TODO: Both
                      'Desires': ('Who desires to {obj}? Name {n}.','What does {subj} desire to do? Name {n}.'), # TODO: Both
                      'HasA': ('What thing has {obj}? Name {n}.','What does {subj} have? Name {n}.'), # TODO: Both
                      'HasFirstSubevent': ('What is the event that causes you to {obj}? Name {n}.','What happens when you {subj}? Name {n}.'), # TODO: Both
                      'HasPrerequisite': ('What needs to happen before you {subj}? Name {n}.','What does {subj} have as a prerequisite? Name {n}.'), # TODO: Find Subject
                      'HasProperty': ('',''),
                      'HasSubevent': ('',''),
                      'IsA': ('',''),
                      'MadeOf': ('',''),
                      'MotivatedByGoal': ('',''),
                      'NotCapableOf': ('',''),
                      'NotHasProperty': ('',''),
                      'NotIsA': ('',''),
                      'PartOf': ('',''),
                      'ReceivesAction': ('',''),
                      'RelatedTo': ('',''),
                      'UsedFor': ('','')}