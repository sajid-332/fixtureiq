"""
FixtureIQ Stage 6.3

Poisson Scoreline Probability Engine

Functions:
    - Calculate goal probability
    - Generate scoreline matrix
    - Return top scorelines
"""


import math
import pandas as pd



# -------------------------------------------------
# Configuration
# -------------------------------------------------

MAX_GOALS = 6



# -------------------------------------------------
# Poisson probability
# -------------------------------------------------

def goal_probability(
    goals,
    lambda_value
):
    """
    Calculate probability of scoring
    exactly X goals using Poisson.

    Formula:

    P(X) =
        (e^-λ * λ^X) / X!

    """

    return (

        math.exp(-lambda_value)

        *
        (lambda_value ** goals)

        /

        math.factorial(goals)

    )



# -------------------------------------------------
# Scoreline Matrix
# -------------------------------------------------

def generate_score_matrix(
    home_lambda,
    away_lambda,
    max_goals=MAX_GOALS
):
    """
    Generate complete score probability matrix.

    Example:

            Away

          0     1     2

    H 0
      1
      2

    """


    matrix = []


    for home_goals in range(
        max_goals + 1
    ):


        for away_goals in range(
            max_goals + 1
        ):


            home_prob = goal_probability(
                home_goals,
                home_lambda
            )


            away_prob = goal_probability(
                away_goals,
                away_lambda
            )


            score_probability = (

                home_prob

                *

                away_prob

            )


            matrix.append({

                "HomeGoals":
                    home_goals,


                "AwayGoals":
                    away_goals,


                "Probability":
                    score_probability

            })


    df = pd.DataFrame(matrix)


    # Convert to percentage

    df["ProbabilityPercent"] = (

        df["Probability"]

        *
        100

    )


    return df



# -------------------------------------------------
# Top scorelines
# -------------------------------------------------

def get_top_scorelines(
    score_matrix,
    top_n=5
):
    """
    Return highest probability scorelines.
    """


    result = (

        score_matrix

        .sort_values(
            "Probability",
            ascending=False
        )

        .head(top_n)

        .copy()

    )


    return result[
        [
            "HomeGoals",
            "AwayGoals",
            "ProbabilityPercent"
        ]
    ]



# -------------------------------------------------
# Probability check
# -------------------------------------------------

def probability_sum(
    score_matrix
):
    """
    Check total probability captured
    by score matrix.
    """

    return (

        score_matrix["Probability"]

        .sum()

        *
        100

    )



# -------------------------------------------------
# Test example
# -------------------------------------------------

if __name__ == "__main__":


    # Example:

    home_lambda = 1.65

    away_lambda = 1.35



    matrix = generate_score_matrix(
        home_lambda,
        away_lambda
    )



    print("\nTop Scorelines")
    print("----------------")


    print(
        get_top_scorelines(
            matrix,
            top_n=5
        )
    )



    print("\nProbability captured:")

    print(
        round(
            probability_sum(matrix),
            2
        ),
        "%"
    )