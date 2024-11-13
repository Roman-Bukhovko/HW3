from dataclasses import dataclass
import logging
import sqlite3
from typing import Any

from meal_max.utils.sql_utils import get_db_connection
from meal_max.utils.logger import configure_logger
from meal_max.utils.random_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Meal:
    id: int
    meal: str
    cuisine: str
    price: float
    difficulty: str

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price must be a positive value.")
        if self.difficulty not in ['LOW', 'MED', 'HIGH']:
            raise ValueError("Difficulty must be 'LOW', 'MED', or 'HIGH'.")


def create_meal(meal: str, cuisine: str, price: float, difficulty: str) -> None:
    """
    Creates a new meal and adds it to the database. 

    Args:
        meal (str): The name of the meal. 
        cuisine (str): The cuisine of the meal. 
        price (float): The cost of the meal. 
        difficulty (str): The level of difficulty of creating the meal. 

    Raises:
        ValueError: If price or difficulty are invalid.
        sqlite3.IntegrityError: If meal with the same name already exists.
        sqlite3.Error: For any other database errors.
    """
    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError(f"Invalid price: {price}. Price must be a positive number.")
    if difficulty not in ['LOW', 'MED', 'HIGH']:
        raise ValueError(f"Invalid difficulty level: {difficulty}. Must be 'LOW', 'MED', or 'HIGH'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meals (meal, cuisine, price, difficulty)
                VALUES (?, ?, ?, ?)
            """, (meal, cuisine, price, difficulty))
            conn.commit()

            logger.info("Meal successfully added to the database: %s", meal)

    except sqlite3.IntegrityError:
        logger.error("Duplicate meal name: %s", meal)
        raise ValueError(f"Meal with name '{meal}' already exists")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def delete_meal(meal_id: int) -> None:
    """
    Soft deletes a meal from the database by marking it as deleted. 

    Args:
        meal_id (int): The ID of the meal.

    Raises:
        ValueError: If the meal with the given ID does not exist or is already marked as deleted.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM meals WHERE id = ?", (meal_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Meal with ID %s has already been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
            except TypeError:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

            cursor.execute("UPDATE meals SET deleted = TRUE WHERE id = ?", (meal_id,))
            conn.commit()

            logger.info("Meal with ID %s marked as deleted.", meal_id)

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_leaderboard(sort_by: str="wins") -> dict[str, Any]:
    """
    Retrieves all meals that are not marked as deleted from the database.

    Args:
        sort_by (str): If "wins", sort the meals by win_pct in descending order.

    Returns:
        dict[str]: A dictionary of strings representing all non-deleted meals with wins.

    Logs:
        Warning: If the database is empty.
    """
    query = """
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    elif sort_by == "price":
        query += "ORDER BY price DESC"
    else:
        logger.error("Invalid sort_by parameter: %s", sort_by)
        raise ValueError("Invalid sort_by parameter: %s" % sort_by)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                logger.warning("The leaderboard is empty.")
                return []

            leaderboard = []
            for row in rows:
                meal = [
                    {
                        'id': row[0],
                        'meal': row[1],
                        'cuisine': row[2],
                        'price': row[3],
                        'difficulty': row[4],
                        "battles": row[5],
                        "wins": row[6],
                        "win_pct": row[7]
                    }
                ]
                leaderboard.append(meal)

            logger.info("Leaderboard retrieved successfully")
            return leaderboard

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_meal_by_id(meal_id: int) -> Meal:
    """
    Retrieves a meal from the database by its meal ID.

    Args:
        meal_id (int): The ID of the meal to retrieve.

    Returns:
        Meal: The Meal object corresponding to the meal_id.

    Raises:
        ValueError: If the meal is not found or is marked as deleted.
        sqlite3.Error: If any database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?", (meal_id,))
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Meal with ID %s has been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
                return Meal(id=row[0], meal=row[1], cuisine=row[2], price=row[3], difficulty=row[4])
            else:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def get_meal_by_name(meal_name: str) -> Meal:
    """
    Retrieves a meal from the database by its name.

    Args:
        meal_name (str): The name of the meal.

    Returns:
        Meal: The Meal object corresponding to the name.

    Raises:
        ValueError: If the meal is not found or is marked as deleted.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?", (meal_name,))
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Meal with name %s has been deleted", meal_name)
                    raise ValueError(f"Meal with name {meal_name} has been deleted")
                return Meal(id=row[0], meal=row[1], cuisine=row[2], price=row[3], difficulty=row[4])
            else:
                logger.info("Meal with name %s not found", meal_name)
                raise ValueError(f"Meal with name {meal_name} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e
"""

"""
def get_random_meal() -> Meal:
    """
    Retrieves a random meal from the database.

    Returns:
        Meal: A randomly selected Meal object.

    Raises:
        ValueError: If the database is empty.
    """
    try:
        leaderboard = get_leaderboard("wins")

        if not leaderboard:
            logger.info("Cannot retrieve random meal because the meal database is empty.")
            raise ValueError("The meal database is empty.")

        # Get a random index using the random.org API
        random_index = get_random(len(leaderboard))
        logger.info("Random index selected: %d (total meals: %d)", random_index, len(leaderboard))

        # Return the meal at the random index, adjust for 0-based indexing
        meal_data = leaderboard[random_index - 1]
        return Meal(
            id=meal_data["id"],
            meal=meal_data["meal"],
            cuisine=meal_data["cuisine"],
            price=meal_data["price"],
            difficulty=meal_data["difficulty"],
            battles=meal_data["battles"],
            wins=meal_data["wins"],
            win_pct=meal_data["win_pct"]
        )

    except Exception as e:
        logger.error("Error while retrieving random meal: %s", str(e))
        raise e

def update_meal_stats(meal_id: int, result: str) -> None:
    """
    Increments the battles of a meal by meal ID.

    Args:
        meal_id (int): The ID of the meal whose battles should be incremented.
        result (str): The results of a meal from a battle. 

    Raises:
        ValueError: If the meal does not exist or is marked as deleted.
        sqlite3.Error: If there is a database error.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM meals WHERE id = ?", (meal_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Meal with ID %s has been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
            except TypeError:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

            if result == "wins":
                cursor.execute("UPDATE meals SET wins = wins + 1, battles = battles + 1, win_pct = wins/battles * 1.0 WHERE id = ?", (meal_id,))
            else:
                raise ValueError(f"Invalid result: {result}. Expected 'wins' or 'loss'.")

            conn.commit()

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e
