# budget-manager
App to track spending and budget

## Easy setup
1. Download run.sh file
2. open terminal (search in search bar)
3. Run the following commands:<br>
`cd ~/Downloads`<br>
`chmod +x run.sh`<br>
`./run.sh` <br>
**NOTE:** must be logged in as an administrator account

## How to use:
### Data Entry
Use the data entry page to manually enter transactions, upload a csv file, or enter your budgets.

#### CSV file
CSV upload is used to buld upload transactions. Required columns are "Date", "Description"\*, "Code"\*, "Amount", "Category" <br>
**Note**: * means value can be empty for that column <br>
Try to keep date formats Day-Month-Year, otherwise the date might be wrongly inferred. You can also use the full date (e.g January 1 2023).

### Monthly summary
This page is for generating information about how your spending was, vs what your bduget was.

### Budget
Set a budget for each category. If multiple budgets exist for the same category, the one with the most recent date before the transaction of that category will be used.


## Setup for dev
- Install python 3.11 or higher. Important for mac to make sure that you are using compatible version of tkinter to avoid this error
`DEPRECATION WARNING: The system version of Tk is deprecated and may be removed in a future release. Please don't rely on it. Set TK_SILENCE_DEPRECATION=1 to suppress this warning.`
- Setup a virtual environment: `python3.11 -m venv venv`
- Activate virtual environment: `. venv/bin/activate`
- `pip install -r requirements.txt`
- May need to run `brew install python-tk`
- copy .env.example to .env.dev or .env.prod, and fill in the values
- Run setup.py file to create database tables: `python setup.py`
- Run main.py: `python main.py` <br>
    **Note:** By default, the app wil run in dev mode. To run in prod mode run: `python main.py -p`

### Recommended extensions for VSCode
- python
- sqlite
- pylint
- github copilot
