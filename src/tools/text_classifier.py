# import torch
# from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
# from torch.utils.data import DataLoader, TensorDataset


# # class TextClassifier:
# #     def __init__(self, model_name="distilbert-base-uncased") -> None:
# #         self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_name)
# #         self.model = DistilBertForSequenceClassification.from_pretrained(model_name)

# #         # set to use the GPU if available
# #         self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# #         self.model.to(self.device)

# #     def predict(self, text, labels):
# #         # tokenize the text
# #         inputs = self.tokenizer(
# #             text, return_tensors="pt", padding=True, truncation=True
# #         )
# #         inputs.to(self.device)

# #         # get the prediction from the model
# #         outputs = self.model(**inputs)
# #         logits = outputs.logits
# #         predicted_label_id = torch.argmax(logits, dim=1).item()
# #         predicted_label = labels[predicted_label_id]
# #         print(predicted_label)

# #         # return the predicted label
# #         return predicted_label


# #     def predict2(self, texts, labels):
# #         # Tokenize the text data
# #         encoded_data = self.tokenizer(
# #             texts, padding=True, truncation=True, return_tensors="pt"
# #         )

# #         # Encode the labels as integers (you can use label encoders or a simple dictionary for this)
# #         label_to_id = {v: i for i, v in enumerate(labels)}
# #         labels = [label_to_id[label] for label in labels]

# #         # Create a DataLoader for batch processing
# #         input_data = TensorDataset(
# #             encoded_data.input_ids, encoded_data.attention_mask, torch.tensor(labels)
# #         )
# #         batch_size = 32
# #         dataloader = DataLoader(input_data, batch_size=batch_size, shuffle=False)

# #         # Make predictions
# #         self.model.eval()
# #         predictions = []

# #         with torch.no_grad():
# #             for batch in dataloader:
# #                 input_ids, attention_mask, labels = batch
# #                 input_ids, attention_mask, labels = (
# #                     input_ids.to(self.device),
# #                     attention_mask.to(self.device),
# #                     labels.to(self.device),
# #                 )

# #                 outputs = self.model(input_ids, attention_mask=attention_mask)
# #                 logits = outputs.logits
# #                 predicted_labels = torch.argmax(logits, dim=1).cpu().numpy()
# #                 predictions.extend(predicted_labels)

# #         # Map the predicted labels back to their original class names
# #         id_to_label = {v: k for k, v in label_to_id.items()}
# #         predicted_class_names = [id_to_label[pred] for pred in predictions]

# #         # Now, predicted_class_names contains the predicted classes for each input line
# #         return predicted_class_names

# #     def predict_many(self, texts):
# #         # tokenize the text
# #         inputs = self.tokenizer(texts, return_tensors="pt", padding=True)
# #         inputs.to(self.device)

# #         # get the prediction from the model
# #         outputs = self.model(**inputs)
# #         logits = outputs.logits
# #         predictions = torch.argmax(logits, dim=1).flatten()

# #         # return the prediction
# #         return predictions.tolist()

import openai

API_KEY = "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"


class TextClassifier:
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
