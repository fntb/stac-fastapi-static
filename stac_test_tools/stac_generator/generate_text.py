import random
import numpy as np

np.random.default_rng().binomial(20, 0.5)


def generate_text(sentence_count: int = np.random.default_rng().binomial(20, 0.5)):
    sentences = []

    for sentence_i in range(sentence_count):
        word_count = np.random.default_rng().poisson(3)
        words = []

        for word_i in range(word_count):
            word = "".join(
                random.choices(
                    "eariotnslcudpmhgbfywkvxzjq",
                    k=np.random.default_rng().poisson(3)
                )
            )
            words.append(word)

        sentence = " ".join(words) + "."
        sentence = sentence.capitalize()

        sentences.append(sentence)

    return " ".join(sentences)


def generate_title_and_description_props():
    title = generate_text(1)
    description = generate_text()

    return {
        "title": title,
        "description": "# " + title + "\n\n" + description
    }
