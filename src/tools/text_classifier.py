from abc import ABC, abstractmethod
import openai
from transformers import pipeline


API_KEY = "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"


class TextClassifier(ABC):
    """
    Abstract class for text classifier
    """

    @abstractmethod
    def predict(self, text, labels):
        """
        Given a text and a list of labels, predict the label for the text
        """
        pass

    @abstractmethod
    def predict_batch(self, texts, labels):
        """
        Given a list of texts and a list of labels, predict the labels for the texts
        """
        pass


class GPTClassifier(TextClassifier):
    """
    GPT-3 Text Classifier
    given a list of text, predict the label for each text
    """

    def __init__(self, model="gpt-3.5-turbo-instruct") -> None:
        openai.api_key = API_KEY
        self.model = model
        self.prompt = """
            You will be provided with a description of a transaction,
            and your task is to classify its cateogry as  one of the below.
            In your answer, ONLY write the category name, do not write anything else!

            CATEGORIES

            ---

            Description: DESCRIPTION

            ---
            Cateogry is:
        """.strip()
        self.max_tokens = 5

    def predict(self, text, labels):
        print(text, labels)
        prompt = self.prompt.replace("CATEGORIES", ", ".join(labels))
        prompt = prompt.replace("DESCRIPTION", text)
        response = openai.Completion.create(
            prompt=prompt,
            temperature=0,
            max_tokens=self.max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            model=self.model,
        )
        print(response)
        predicted_label = response.choices[0].text.strip()

        print(predicted_label)
        return predicted_label

    def predict_batch(self, texts, labels):
        prompts = []
        for text in texts:
            prompt = self.prompt.replace("CATEGORIES", ", ".join(labels))
            prompt = prompt.replace("DESCRIPTION", text)
            prompts.append(prompt)

        response = openai.Completion.create(
            prompt=prompts,
            max_tokens=self.max_tokens,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            model=self.model,
        )
        # The response is sometimes Category: cateogry, sometimes Category is: cateogry, so handle the cases
        predicted_labels = []
        for choice in response.choices:
            predicted_label = choice.text.strip()
            predicted_label = predicted_label.replace("Category:", "")
            predicted_label = predicted_label.replace("Category is:", "")
            predicted_label = predicted_label.strip()
            predicted_labels.append(predicted_label)
        print(predicted_labels)
        return predicted_labels


class SimpleClassifier(TextClassifier):
    """
    This classifier will be used to classify the text using NLP techniques.
    It uses a pre-trained model from huggingface.
    """

    def __init__(self, model="facebook/bart-large-mnli") -> None:
        self.pipe = pipeline(task="zero-shot-classification", model=model)

    def predict(self, text, labels):
        result = self.pipe(text, labels)
        predicted_label = result["labels"][0]
        return predicted_label

    def predict_batch(self, texts, labels):
        result = self.pipe(texts, labels)
        predicted_labels = [r["labels"][0] for r in result]
        return predicted_labels
    

c = SimpleClassifier()
print(c.predict_batch(["I want to buy a car", "I want to sell a car"], ["buy", "sell"]))
