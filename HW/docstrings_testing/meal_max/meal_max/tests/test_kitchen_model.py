from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    get_random_meal,
    update_meal_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the database."""

    # Call the function to create a new meal
    create_meal(meal="Meal Name", cuisine="Cuisine Type", price=8.99, difficulty="LOW")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name", "Cuisine Type", 8.99, "LOW")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate meal (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Meal Name' already exists"):
        create_meal(meal="Meal Name", cuisine="Cuisine Type", price=8.99, difficulty="LOW")

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (e.g., negative price)"""

    # Attempt to create a meal with a negative duration
    with pytest.raises(ValueError, match="Invalid price: -8.99. Price must be a positive number."):
        create_meal("Meal Name", "Cuisine Type", -8.99, "LOW")

    # Attempt to create a meal with a non-integer duration
    with pytest.raises(ValueError, match="Invalid price: a. Price must be a positive number."):
        create_meal("Meal Name", "Cuisine Type", "a", "LOW")

def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty."""

    # Attempt to create a meal with an invalid difficulty
    with pytest.raises(ValueError, match="Invalid difficulty level: INVALID. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal("Meal Name", "Cuisine Type", 8.99, "INVALID")

def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the database by meal ID."""

    # Simulate that the meak exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_meal function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        delete_meal(999)

######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine Type", 8.99, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Type", 8.99, "LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_id_bad_id(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists (meal = "Meal Name")
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine Type", 8.99, "LOW", False)

    # Call the function and check the result
    result = get_meal_by_name("Meal Name")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine Type", 8.99, "LOW")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name",)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_leaderboard(mock_cursor):
    """Test retrieving all meals that are not marked as deleted."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Meal A", "Cuisine A", 8.99, "LOW"),
        (2, "Meal B", "Cuisine B", 9.99, "MED"),
        (3, "Meal C", "Cuisine C", 10.99, "HIGH")
    ]

    # Call the get_leaderboard function
    leaderboard = get_leaderboard()

    # Ensure the results match the expected output
    expected_result = [
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 8.99, "difficulty": "LOW"},
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 9.99, "difficulty": "MED"},
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 10.99, "difficulty": "HIGH"}
    ]

    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty
        FROM meals
        WHERE deleted = FALSE
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_empty(mock_cursor, caplog):
    """Test that retrieving leaderboard returns an empty list when it is empty and logs a warning."""

    # Simulate that the leaderboard is empty (no meals)
    mock_cursor.fetchall.return_value = []

    # Call the get_leaderboard function
    result = get_leaderboard()

    # Ensure the result is an empty list
    assert result == [], f"Expected empty list, but got {result}"

    # Ensure that a warning was logged
    assert "The leaderboard is empty." in caplog.text, "Expected warning about empty leaderboard not found in logs."

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty FROM meals WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_all_meals_ordered(mock_cursor):
    """Test retrieving all songs ordered by battles."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        {3, "Meal C", "Cuisine C", 10.99, "HIGH", 10, 4, 0.4},
        {1, "Meal A", "Cuisine A", 8.99, "LOW", 5, 3, 0.6},
        {2, "Meal B", "Cuisine B", 9.99, "MED",  4, 2, 0.5}
    ]

    # Call the get_leaderboard function with sort_by = True
    meals = get_leaderboard(sort_by="price")

    # Ensure the results are sorted by wins
    expected_result = [
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 10.99, "difficulty": "HIGH"},
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 9.99, "difficulty": "MED"},
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 8.99, "difficulty": "LOW"}
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty
        FROM meals
        WHERE deleted = FALSE
        ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_random_meal(mock_cursor, mocker):
    """Test retrieving a random meal."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Meal A", "Cuisine A", 8.99, "LOW"),
        (2, "Meal B", "Cuisine B", 9.99, "MED"),
        (3, "Meal C", "Cuisine C", 10.99, "HIGH")
    ]

    # Mock random number generation to return the 2nd meal
    
    mock_random = mocker.patch("meal_max.models.kitchen_model.get_random", return_value=2)

    # Call the get_random_meal method
    result = get_random_meal()

    # Expected result based on the mock random number and fetchall return value
    expected_result = Meal(2, "Meal B", "Cuisine B", 9.99, "MED")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure that the random number was called with the correct number of songs
    mock_random.assert_called_once_with(3)

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty FROM meals WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_random_meal_empty(mock_cursor, mocker):
    """Test retrieving a random meal when empty."""

    # Simulate that the catalog is empty
    mock_cursor.fetchall.return_value = []

    # Expect a ValueError to be raised when calling get_random_song with an empty catalog
    with pytest.raises(ValueError, match="The meal database is empty"):
        get_random_meal()

    # Ensure that the random number was not called since there are no meals
    mocker.patch("meal_max.models.kitchen_model.get_random").assert_not_called()

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty FROM meals WHERE deleted = FALSE")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_update_meal_stats(mock_cursor):
    """Test updating the stats of a meals."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with a sample meal ID
    meal_id = 1
    update_meal_stats(meal_id, 8.99)

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET price = price + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

### Test for Updating a Deleted Meal:
def test_update_wins_deleted_meal(mock_cursor):
    """Test error when trying to update play count for a deleted meal."""

    # Simulate that the meal exists but is marked as deleted (id = 1)
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, price=8.99)

    # Ensure that no SQL query for updating play count was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))