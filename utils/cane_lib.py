

# Quick lil function to check if any keywords are in a piece of text
def keyword_check(phrase, keywords):
    for k in keywords:
        if str.lower(k) in str.lower(phrase):
            return True

    return False
