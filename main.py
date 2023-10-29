from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from db.dbmanager import DBManager

class FormApp(App):
    def build(self):
        self.db = DBManager()
        self.form_fields = ["Date", "Description", "Amount", "Category", "Code"]
        self.kivy_fields = []
        
        layout = BoxLayout(orientation="vertical", padding=20)
        
        for field in self.form_fields:
            label = Label(text=field, font_size=12, color=(0, 0, 0, 1))
            layout.add_widget(label)
            
            text_input = TextInput()
            layout.add_widget(text_input)
            self.kivy_fields.append(text_input)
        
        submit_button = Button(text="Submit", font_size=12)
        submit_button.bind(on_press=self.submit)
        layout.add_widget(submit_button)

        return layout

    def submit(self, instance):
        data = [field.text for field in self.kivy_fields]
        for text_input in self.kivy_fields:
            print(text_input.text)
            text_input.text = ""

        self.db.insert(
            "INSERT INTO transactions (date, description, amount, category, code) VALUES (?, ?, ?, ?, ?)",
            data,
        )

if __name__ == "__main__":
    with DBManager() as db:
        transactions = db.select("SELECT * FROM transactions", [])
        for transaction in transactions:
            print(transaction)
    FormApp().run()
    # show all transactionsß

