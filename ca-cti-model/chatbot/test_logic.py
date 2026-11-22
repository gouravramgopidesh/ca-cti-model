from main import cosine,keywords,Question
assert abs(cosine([1,0],[1,0])-1)<1e-6
assert cosine([1,0],[0,1])==0
assert "ransomware" in keywords("Analyze ransomware on Windows")
assert Question(message="Check phishing").platform=="General"
print("PASS: chatbot standalone logic")
