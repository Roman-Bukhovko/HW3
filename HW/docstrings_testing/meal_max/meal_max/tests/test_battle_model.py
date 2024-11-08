import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture()

def battle_model():
    """Fixture to provide a new instance of BattleModel for each test. """
    return BattleModel()

#look into another fixture equivalent of update_play_count?
#might need something else here for battle

@pytest.fixture
def sample_meal1():
    return Meal(1, 'Meal 1', 'Cuisine 1', 1, 'LOW')

@pytest.fixture
def sample_meal2():
    return Meal(2, 'Meal 2', 'Cuisine 2', 2, 'MED')

#this might be wrong
@pytest.fixture
def sample_battle(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]


########################################
# Test Cases
