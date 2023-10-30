import tkinter as tk
from datetime import datetime

class FormValidator:
    def __init__(self, form_fields: list[dict[str, str]]):
        self.form_fields = form_fields

    def validate(self, data: dict[str, tk.Entry]) -> dict[str, str]:
        errors = {}
        for field_info in self.form_fields:
            field_name = field_info["name"]
            value = data[field_name].get()
            if field_info["type"] == "date":
                if not self.validate_date(value):
                    errors[field_name] = "Invalid date"
                
            elif field_info["type"] == "number":
                if not value.replace(".", "").isdigit():
                    errors[field_name] = "Invalid number"

        return errors
    
    def validate_date(self, date_str: str) -> bool:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now()
            if date > today:
                return False
            return True
        except ValueError:
            return False

class Form:
    FORM_FIELDS = [
        # consider making class form field instead of dict
        {
            "name": "Date",
            "type": "date",
            "required": True,
        },
        {
            "name": "Description",
            "type": "text",
            "required": True,
        },
        {
            "name": "Amount",
            "type": "number",
            "required": True,
        },
        {
            "name": "Category",
            "type": "text",
            "required": True,
        },
        {
            "name": "Code",
            "type": "text",
            "required": False,
        }
    ]

    def __init__(self, master: tk.Tk):
        self.master = master
        self.form_fields = [field["name"] for field in Form.FORM_FIELDS]
        self.tk_fields = {}
        self.error_labels = {}
        self.form = tk.Frame(self.master)
        self.form.pack(pady=20)
        self.validator = FormValidator(Form.FORM_FIELDS)
        self.create_form()

    def create_form(self):
        for i, field_info in enumerate(Form.FORM_FIELDS):
            field_name = field_info["name"]
            tk_label = tk.Label(self.form, text=field_name, font=("Arial", 12), fg="white")
            tk_label.grid(row=i * 2, column=0, sticky='w', padx=10, pady=10)
            tk_field = tk.Entry(self.form)
            tk_field.grid(row=i * 2 + 1, column=0, padx=10, pady=10, sticky='w')
            self.tk_fields[field_name] = tk_field

            error_label = tk.Label(self.form, text="", font=("Arial", 10), fg="red")
            error_label.grid(row=i * 2, column=0, padx=10)
            self.error_labels[field_name] = error_label

        submit_button = tk.Button(self.form, text="Submit", command=self.submit, font=("Arial", 12), bg="white")
        submit_button.grid(row=len(Form.FORM_FIELDS) * 2, columnspan=3, padx=20, pady=5)

    def submit(self):
        data = {}
        errors = self.validator.validate(self.tk_fields)

        for field_name, error_message in errors.items():
            tk_field = self.tk_fields[field_name]
            error_label = self.error_labels[field_name]
            tk_field.config(highlightbackground="red", highlightcolor="red")
            error_label.config(text=error_message)

        if not errors:
            # Data is valid, proceed with insertion
            self.db.insert(
                "INSERT INTO transactions (date, description, amount, category, code) VALUES (?, ?, ?, ?, ?)",
                list(data.values()),
            )
            self.clear_form()

    def clear_form(self):
        for field_name, tk_field in self.tk_fields.items():
            error_label = self.error_labels[field_name]
            tk_field.config(highlightbackground="SystemButtonFace", highlightcolor="SystemButtonFace")
            tk_field.delete(0, "end")
            error_label.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    form = Form(root)

    root.mainloop()
