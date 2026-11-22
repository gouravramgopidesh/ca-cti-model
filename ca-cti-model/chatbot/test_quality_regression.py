from main import classify_intent, requested_lab, exact_arithmetic, effective_mode, is_fresh_topic
assert classify_intent('What are the latest threats stored in MongoDB?')=='latest'
assert classify_intent('What are the latest articles in my database?')=='latest'
assert effective_mode('auto','Explain Lab 17 and MongoDB vector search')=='cti'
assert requested_lab('Explain Lab 17 and MongoDB vector search')==17
assert requested_lab('Summarize Lab 4')==4
assert requested_lab('Explain MongoDB') is None
assert exact_arithmetic('What is 25 + 75?')=='25 + 75 = 100'
assert is_fresh_topic('Explain Lab 17 and MongoDB vector search')
print('Regression checks passed')
