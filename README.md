# budget-manager
App to track spending and budget

## Setup
- Install python 3.11. At least a version higher than 3.10.0 is needed for pyinstaller to work (3.10.0 has a bug in it)
Important for mac to make sure that you are using compatible version of tkinter to avoid this error
`DEPRECATION WARNING: The system version of Tk is deprecated and may be removed in a future release. Please don't rely on it. Set TK_SILENCE_DEPRECATION=1 to suppress this warning.`
- Setup a virtual environment: `python3.10 -m venv venv`
- Activate virtual environment: `. venv/bin/activate`
- `pip install -r requirements.txt`
- Run setup.py file to create database tables: `python setup.py`
- Run main.py: `python main.py`

### Recommended extensions for VSCode
- python
- sqlite
- pylint
- github copilot

## Bundle code to one file
I use the auto-py-to-exe library, which is basically just a GUI on top of the pyinstaller command.
Just run auto-py-to-exe in a console, and select main.py file, and follow instructions.
OR, run this command:
`pyinstaller --onefile --windowed --noconfirm main.py`