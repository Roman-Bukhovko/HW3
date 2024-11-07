#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Meal Management
#
##########################################################

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal, $cuisine, $price, $difficulty)..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal_by_id() {
  id=$1

  echo "Deleting meal by ID ($id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($id)."
  else
    echo "Failed to delete meal by ID ($id)."
    exit 1
  fi
}

get_all_meals() {
  echo "Getting all meals..."
  response=$(curl -s -X GET "$BASE_URL/get-all-meals")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All meals retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meals JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meals."
    exit 1
  fi
}

get_meal_by_id() {
  id=$1

  echo "Getting meal by ID ($id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($id)."
    exit 1
  fi
}

get_meal_by_name() {
  meal_name=$1

  echo "Getting meal by name (Meal Name: '$meal_name')..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-from-name?meal_name=$(echo $meal_name | sed 's/ /%20/g')")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (by name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name."
    exit 1
  fi
}

get_random_meal() {
  echo "Getting a random meal from the catalog..."
  response=$(curl -s -X GET "$BASE_URL/get-random-meal")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Random meal retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Random Meal JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get a random meal."
    exit 1
  fi
}

############################################################
#
# Arrange Leaderboard
#
############################################################

move_meal_to_top() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Moving meal ($meal, $cuisine, $price, $difficulty) to the top of the leaderboard..."
  response=$(curl -s -X POST "$BASE_URL/move-meal-to-top" \
    -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal\", \"cuisine\": \"$cuisine\", \"price\": $price, \"difficulty\": \"$difficulty\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal moved to the beginning successfully."
  else
    echo "Failed to move meal to the top."
    exit 1
  fi
}

move_meal_to_bottom() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Moving meal ($artist - $title, $year) to the bottom of the leaderboard..."
  response=$(curl -s -X POST "$BASE_URL/move-meal-to-bottom" \
    -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal\", \"cuisine\": \"$cuisine\", \"price\": $price, \"difficulty\": \"$difficulty\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal moved to the bottom successfully."
  else
    echo "Failed to move meal to the bottom."
    exit 1
  fi
}

######################################################
#
# Leaderboard
#
######################################################

# Function to get the meal leaderboard 
get_leaderboard() {
  echo "Getting meak leaderboard..."
  response=$(curl -s -X GET "$BASE_URL/get-leaderboard")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get leaderboard."
    exit 1
  fi
}


# Health checks
check_health
check_db

# Create meals
create_meal "Borscht" "Ukrainian" 10.99 "MED"
create_meal "Sushi" "Japanese" 12.99 "HIGH"
create_meal "Burger" "American" 9.99 "LOW"

delete_meal_by_id 2
get_all_meals

get_meal_by_id 1
get_meal_by_name "Borscht"
get_random_meal

get_leaderboard

echo "All tests passed successfully!"
