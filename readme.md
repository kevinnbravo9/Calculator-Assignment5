# Module 5 - Advanced Calculator

This project is an advanced calculator application created in Python. It uses object-oriented programming, design patterns, pandas for calculation history, environment variables for configuration, and pytest for testing.

## Features

The calculator includes the following operations:

- Addition
- Subtraction
- Multiplication
- Division
- Power
- Root

It also includes:

- Calculation history
- Save and load history using CSV files
- Undo and redo
- Auto-save
- Input validation
- Error handling
- REPL interface

## Design Patterns

This project uses several design patterns:

- Factory Pattern - Creates the correct operation based on the user input.
- Strategy Pattern - Allows different calculation operations to be used.
- Observer Pattern - Monitors calculation events such as logging and saving history.
- Memento Pattern - Saves the calculator state for undo and redo.
- Facade Pattern - Provides a simpler interface for using the calculator.

## Project Setup

Clone the repository:

```bash
git clone https://github.com/kevinnbravo9/Calculator-Assignment5.git
```

Move into the project folder:

```bash
cd module5_is601
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the main project folder and add:

```env
CALCULATOR_MAX_HISTORY_SIZE=100
CALCULATOR_AUTO_SAVE=true
CALCULATOR_DEFAULT_ENCODING=utf-8
```

## Running the Calculator

Run the calculator with:

```bash
python3 main.py
```

The calculator uses a REPL interface that allows the user to continuously enter commands.

Some available commands include:

- `help`
- `history`
- `clear`
- `undo`
- `redo`
- `save`
- `load`
- `exit`

## Testing

Run all tests using:

```bash
pytest
```

To run the tests and check test coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

The project has 100% test coverage.

## GitHub Actions

GitHub Actions is used to automatically run the tests when changes are pushed to the repository. The workflow also checks test coverage to make sure the project maintains 100% coverage.