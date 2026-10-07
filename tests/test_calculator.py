import datetime
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import Mock, patch, PropertyMock
from decimal import Decimal
from tempfile import TemporaryDirectory
from app.calculator import Calculator
from app.calculator_repl import calculator_repl
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError
from app.history import LoggingObserver, AutoSaveObserver
from app.operations import OperationFactory

# Fixture to initialize Calculator with a temporary directory for file paths
@pytest.fixture
def calculator():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = CalculatorConfig(base_dir=temp_path)

        # Patch properties to use the temporary directory paths
        with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
             patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
             patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
             patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:
            
            # Set return values to use paths within the temporary directory
            mock_log_dir.return_value = temp_path / "logs"
            mock_log_file.return_value = temp_path / "logs/calculator.log"
            mock_history_dir.return_value = temp_path / "history"
            mock_history_file.return_value = temp_path / "history/calculator_history.csv"
            
            # Return an instance of Calculator with the mocked config
            yield Calculator(config=config)

# Test Calculator Initialization

def test_calculator_initialization(calculator):
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []
    assert calculator.operation_strategy is None

# Test Logging Setup

@patch('app.calculator.logging.info')
def test_logging_setup(logging_info_mock):
    with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
         patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file:
        mock_log_dir.return_value = Path('/tmp/logs')
        mock_log_file.return_value = Path('/tmp/logs/calculator.log')
        
        # Instantiate calculator to trigger logging
        calculator = Calculator(CalculatorConfig())
        logging_info_mock.assert_any_call("Calculator initialized with configuration")

# Test Adding and Removing Observers

def test_add_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    assert observer in calculator.observers

def test_remove_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    calculator.remove_observer(observer)
    assert observer not in calculator.observers

# Test Setting Operations

def test_set_operation(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    assert calculator.operation_strategy == operation

# Test Performing Operations

def test_perform_operation_addition(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    result = calculator.perform_operation(2, 3)
    assert result == Decimal('5')

def test_perform_operation_validation_error(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    with pytest.raises(ValidationError):
        calculator.perform_operation('invalid', 3)

def test_perform_operation_operation_error(calculator):
    with pytest.raises(OperationError, match="No operation set"):
        calculator.perform_operation(2, 3)

# Test Undo/Redo Functionality

def test_undo(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    assert calculator.history == []

def test_redo(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    calculator.redo()
    assert len(calculator.history) == 1

# Test History Management

@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_history(mock_to_csv, calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.save_history()
    mock_to_csv.assert_called_once()

@patch('app.calculator.pd.read_csv')
@patch('app.calculator.Path.exists', return_value=True)
def test_load_history(mock_exists, mock_read_csv, calculator):
    # Mock CSV data to match the expected format in from_dict
    mock_read_csv.return_value = pd.DataFrame({
        'operation': ['Addition'],
        'operand1': ['2'],
        'operand2': ['3'],
        'result': ['5'],
        'timestamp': [datetime.datetime.now().isoformat()]
    })
    
    # Test the load_history functionality
    try:
        calculator.load_history()
        # Verify history length after loading
        assert len(calculator.history) == 1
        # Verify the loaded values
        assert calculator.history[0].operation == "Addition"
        assert calculator.history[0].operand1 == Decimal("2")
        assert calculator.history[0].operand2 == Decimal("3")
        assert calculator.history[0].result == Decimal("5")
    except OperationError:
        pytest.fail("Loading history failed due to OperationError")
        
            
# Test Clearing History

def test_clear_history(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.clear_history()
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []

# Test REPL Commands (using patches for input/output handling)

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_calculator_repl_exit(mock_print, mock_input):
    with patch('app.calculator.Calculator.save_history') as mock_save_history:
        calculator_repl()
        mock_save_history.assert_called_once()
        mock_print.assert_any_call("History saved successfully.")
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_calculator_repl_help(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")

@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
@patch('builtins.print')
def test_calculator_repl_addition(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nResult: 5")

@patch('builtins.input', side_effect=['clear', 'exit'])
@patch('builtins.print')
def test_calculator_repl_clear(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("History cleared")


@patch('builtins.input', side_effect=['undo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_undo_empty(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Nothing to undo")


@patch('builtins.input', side_effect=['redo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_redo_empty(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Nothing to redo")


@patch('builtins.input', side_effect=['save', 'exit'])
@patch('builtins.print')
def test_calculator_repl_save(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("History saved successfully")


@patch('builtins.input', side_effect=['load', 'exit'])
@patch('builtins.print')
def test_calculator_repl_load(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("History loaded successfully")


@patch('builtins.input', side_effect=['unknown', 'exit'])
@patch('builtins.print')
def test_calculator_repl_unknown_command(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call(
        "Unknown command: 'unknown'. Type 'help' for available commands."
    )


@patch('builtins.input', side_effect=['add', 'cancel', 'exit'])
@patch('builtins.print')
def test_calculator_repl_cancel_first_number(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation cancelled")


@patch('builtins.input', side_effect=['add', '5', 'cancel', 'exit'])
@patch('builtins.print')
def test_calculator_repl_cancel_second_number(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation cancelled")

@patch('builtins.input', side_effect=['undo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_undo_empty(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Nothing to undo")

@patch('builtins.input', side_effect=['redo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_redo_empty(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Nothing to redo")

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
@patch('app.calculator.Calculator.save_history', side_effect=Exception("Save failed"))
def test_calculator_repl_exit_save_error(mock_save, mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Warning: Could not save history: Save failed")

@patch('builtins.input', side_effect=['add', '2', '3', 'history', 'exit'])
@patch('builtins.print')
def test_calculator_repl_history_with_calculation(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nCalculation History:")

@patch('builtins.input', side_effect=['add', '2', '3', 'undo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_undo_success(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation undone")

@patch('builtins.input', side_effect=['add', '2', '3', 'undo', 'redo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_redo_success(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Operation redone")

@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_calculator_repl_help(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")

@patch('builtins.input', side_effect=['clear', 'exit'])
@patch('builtins.print')
def test_calculator_repl_clear(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("History cleared")

@patch('app.calculator.Calculator.save_history', side_effect=Exception("Save failed"))
@patch('builtins.input', side_effect=['save', 'exit'])
@patch('builtins.print')
def test_calculator_repl_save_error(mock_print, mock_input, mock_save):
    calculator_repl()
    mock_print.assert_any_call("Error saving history: Save failed")

@patch('app.calculator.Calculator.load_history', side_effect=Exception("Load failed"))
@patch('builtins.input', side_effect=['load', 'exit'])
@patch('builtins.print')
def test_calculator_repl_load_error(mock_print, mock_input, mock_load):
    calculator_repl()
    mock_print.assert_any_call("Error loading history: Load failed")

@patch('builtins.input', side_effect=['divide', '10', '0', 'exit'])
@patch('builtins.print')
def test_calculator_repl_divide_by_zero(mock_print, mock_input):
    calculator_repl()
    assert any(
        "Error:" in str(call)
        for call in mock_print.call_args_list
    )

@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
@patch('builtins.print')
@patch('app.calculator.Calculator.perform_operation', side_effect=Exception("Test error"))
def test_calculator_repl_unexpected_calculation_error(mock_operation, mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Unexpected error: Test error")

@patch('builtins.input', side_effect=['history', 'exit'])
@patch('builtins.print')
def test_calculator_repl_empty_history(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("No calculations in history")

@patch('builtins.input', side_effect=[KeyboardInterrupt, 'exit'])
@patch('builtins.print')
def test_calculator_repl_keyboard_interrupt(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nOperation cancelled")

@patch('builtins.input', side_effect=EOFError)
@patch('builtins.print')
def test_calculator_repl_eof_error(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nInput terminated. Exiting...")

@patch('builtins.input', side_effect=[Exception("Test error"), 'exit'])
@patch('builtins.print')
def test_calculator_repl_general_error(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("Error: Test error")

@patch('app.calculator_repl.Calculator', side_effect=Exception("Initialization failed"))
@patch('builtins.print')
def test_calculator_repl_initialization_error(mock_print, mock_calculator):
    with pytest.raises(Exception, match="Initialization failed"):
        calculator_repl()

    mock_print.assert_any_call("Fatal error: Initialization failed")

def test_calculator_memento_to_dict():
    from app.calculator_memento import CalculatorMemento

    memento = CalculatorMemento(history=[])
    data = memento.to_dict()

    assert data["history"] == []
    assert "timestamp" in data


def test_calculator_memento_from_dict():
    from app.calculator_memento import CalculatorMemento

    memento = CalculatorMemento(history=[])
    data = memento.to_dict()

    restored = CalculatorMemento.from_dict(data)

    assert restored.history == []
    assert restored.timestamp == memento.timestamp

def test_calculation_string_methods():
    from decimal import Decimal
    from app.calculation import Calculation

    calc = Calculation("Addition", Decimal("2"), Decimal("3"))

    # Cover __str__
    text = str(calc)
    assert "Addition" in text

    # Cover __repr__
    representation = repr(calc)
    assert "Calculation" in representation

    # Cover __eq__ with a non-Calculation object
    assert calc.__eq__("not a calculation") is NotImplemented

def test_calculation_arithmetic_error(monkeypatch):
    from decimal import Decimal
    from app.calculation import Calculation
    from app.exceptions import OperationError
    import pytest

    calc = Calculation("Addition", Decimal("2"), Decimal("3"))

    class BadDecimal(Decimal):
        def __add__(self, other):
            raise ArithmeticError("Test arithmetic error")

    calc.operand1 = BadDecimal("2")

    with pytest.raises(OperationError, match="Calculation failed"):
        calc.calculate()

def test_setup_logging_error(monkeypatch):
    from app.calculator import Calculator
    import pytest

    def raise_error(*args, **kwargs):
        raise Exception("Test logging error")

    monkeypatch.setattr("logging.basicConfig", raise_error)

    with pytest.raises(Exception, match="Test logging error"):
        Calculator()

def test_history_max_size():
    from app.calculator import Calculator
    from app.operations import Addition

    calc = Calculator()
    calc.config.max_history_size = 1

    calc.set_operation(Addition())

    calc.perform_operation("1", "2")
    calc.perform_operation("3", "4")

    assert len(calc.history) == 1

def test_perform_operation_general_exception():
    from app.calculator import Calculator
    from app.exceptions import OperationError
    import pytest

    class BadOperation:
        def execute(self, a, b):
            raise Exception("Test operation failure")

        def __str__(self):
            return "BadOperation"

    calc = Calculator()
    calc.set_operation(BadOperation())

    with pytest.raises(OperationError, match="Operation failed"):
        calc.perform_operation("2", "3")

def test_save_history_error(monkeypatch):
    from app.calculator import Calculator
    from app.exceptions import OperationError
    import pytest

    calc = Calculator()

    def raise_error(*args, **kwargs):
        raise Exception("Test save error")

    monkeypatch.setattr("pandas.DataFrame.to_csv", raise_error)

    with pytest.raises(OperationError, match="Failed to save history"):
        calc.save_history()

def test_load_history_error(monkeypatch):
    from app.calculator import Calculator
    from app.exceptions import OperationError
    import pytest

    calc = Calculator()

    def raise_error(*args, **kwargs):
        raise Exception("Test load error")

    monkeypatch.setattr("pandas.read_csv", raise_error)

    with pytest.raises(OperationError, match="Failed to load history"):
        calc.load_history()

def test_get_history_dataframe_empty():
    from app.calculator import Calculator

    calc = Calculator()
    calc.history = []

    df = calc.get_history_dataframe()

    assert df.empty