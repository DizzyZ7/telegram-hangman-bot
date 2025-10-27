import random

def load_words(path="words.txt"):
    with open(path, "r", encoding="utf-8") as f:
        words = [w.strip() for w in f if w.strip()]
    return words


def choose_word(words):
    return random.choice(words).lower()


def masked_word(word, guessed):
    return " ".join([c if c in guessed else "_" for c in word])


def is_won(word, guessed):
    return all(c in guessed for c in word)
