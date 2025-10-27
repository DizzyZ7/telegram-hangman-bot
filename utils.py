import random
from typing import List, Set

def load_words(lang: str = 'en') -> List[str]:
    path = 'words_en.txt' if lang == 'en' else 'words_ru.txt'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            words = [w.strip().lower() for w in f if w.strip()]
    except FileNotFoundError:
        words = []
    return words

def choose_word(words: List[str]) -> str:
    return random.choice(words).lower() if words else 'python'

def masked_word(word: str, guessed: Set[str]) -> str:
    return ' '.join([c if c in guessed else '_' for c in word])

def is_won(word: str, guessed: Set[str]) -> bool:
    return all(c in guessed for c in word)
