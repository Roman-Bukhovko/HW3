import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture()

def battle_model():
    """Fixture to provide a new instance of BattleModel for each test. """
    return BattleModel()

@pytest.fixture
def sample_meal1():
     """Fixture to provide a new instance of Meal for the second combatant"""
     return Meal(1, 'Meal 1', 'Cuisine 1', 1, 'LOW')

@pytest.fixture
def sample_meal2():
    """Fixture to provide a new instance of Meal for the second combatant"""
    return Meal(2, 'Meal 2', 'Cuisine 2', 2, 'MED')

@pytest.fixture                                                         
def sample_meal3():
    """Fixture to provide a new instance of Meal for a third combatant"""
    return Meal(3, 'Meal 3', 'Cuisine 3', 3, 'HIGH')

########################################
# Prep Combatant Test Cases
########################################

def test_prep_combatant(battle_model, sample_meal1, sample_meal2, sample_meal3):
    """Test preparing two meals into combatants for the battle"""
    """Test addding one meal to empty combatant list"""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.get_combatants()) == 1
    assert battle_model.get_combatants()[0] == sample_meal1

    """Test adding a second meal to combatant list"""
    battle_model.prep_combatant(sample_meal2)
    assert len(battle_model.get_combatants()) == 2
    assert battle_model.get_combatants()[1] == sample_meal2

    
    """Test adding another combatant when list is already full"""
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal3)
    
def test_prep_combatant_duplicates(battle_model, sample_meal1):
    """Test preparing one meal into combatants as duplicates. This should raise no errors"""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.get_combatants()) == 1
    assert battle_model.get_combatants()[0] == sample_meal1

    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.get_combatants()) == 2
    assert battle_model.get_combatants()[1] == sample_meal1

def test_prep_combatant_invalid_meal_price(battle_model):
    """Test preparing an invalid meal to a combatant for a battle."""

    with pytest.raises(ValueError, match="Price must be a positive value."):
        sample_meal_invalid = Meal(4, "Meal Invalid", "Cuisine Invalid", -8.99, "LOW")

def test_get_combatants_empty_list(battle_model):
    """Test retrieving combatants with no combatants in the battle."""

    assert battle_model.get_combatants() == []


def test_get_battle_low_score(battle_model):
    """Test accuracy of battle score for low score meal"""

    low_score_meal = Meal(5, "Low Score", "", 0, "LOW")

    assert battle_model.get_battle_score(low_score_meal) == -3

def test_get_battle_high_score(battle_model):
    """Test accuracy of battle score for high schore meal"""

    high_score_meal = Meal(6, "High Score", "High Cuisine", 100, "HIGH")

    assert battle_model.get_battle_score(high_score_meal) == 1199

def test_clear_combatants_full(battle_model, sample_meal1, sample_meal2):
    """Test that the list of combatants is cleared when full"""

    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    assert len(battle_model.get_combatants()) == 2

    battle_model.clear_combatants()

    assert len(battle_model.get_combatants()) == 0
   
def test_clear_combatants_one(battle_model, sample_meal1):
    """Test that the list of combatants is cleared when only one meal exists"""
    battle_model.prep_combatant(sample_meal1)

    assert len(battle_model.get_combatants()) == 1

    battle_model.clear_combatants()

    assert len(battle_model.get_combatants()) == 0

def test_clear_combatants_empty(battle_model):
    """Test list of combatants is cleared when empty. This should raise no errors"""
    assert len(battle_model.get_combatants()) == 0

    battle_model.clear_combatants()

    assert len(battle_model.get_combatants()) == 0

def test_battle_empty(battle_model):
    """Test battle when there is no combatants. Should raise a ValueError"""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_battle_only_one(battle_model, sample_meal1):
    """Test battle when there is not enough combatants. Should raise a ValueError"""
    battle_model.prep_combatant(sample_meal1)

    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()
def test_battle_sample_meals(battle_model, sample_meal1, sample_meal2, mocker):
    """Test accuracy of battle based on sample meals"""
    
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    
    """checking scores"""

    assert battle_model.get_battle_score(sample_meal1) == 6
    assert battle_model.get_battle_score(sample_meal2) == 16

    mock_random = mocker.patch('meal_max.models.battle_model.get_random', return_value=0.05)
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_db = mocker.patch('meal_max.utils.sql_utils.get_db_connection', return_value=mock_conn)
    
    mock_update_meal_stats = mocker.patch('meal_max.models.kitchen_model.update_meal_stats')
    
    winner = battle_model.battle()

    assert winner == 'Meal 1'

    mock_random.assert_called_once()

