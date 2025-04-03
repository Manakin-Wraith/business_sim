# Python Business Simulation Game

A text-based business simulation game written in Python where you manage a company, make strategic decisions, and compete against an AI opponent to achieve financial success.

## Description

This game simulates running a small manufacturing business turn-by-turn (monthly). You need to manage key aspects of the business including:

*   **Production:** Deciding how many units to produce based on cost, capacity, and expected demand.
*   **Staffing:** Hiring and firing workers, which directly impacts your production capacity and salary expenses.
*   **Pricing:** Setting the price for your product, significantly influencing demand.
*   **Marketing:** Investing to increase product awareness and demand.
*   **Research & Development (R&D):** Investing to improve product quality or reduce production costs, with player choice on breakthroughs.
*   **Finance:** Managing cash flow, taking and repaying loans (with interest), and tracking profitability.

You compete against an AI-controlled competitor who makes its own decisions based on market conditions and its own financial state. The market features dynamic demand influenced by price, quality, marketing, overall trends, and random events. If the AI competitor goes bankrupt, a new one will enter the market to maintain the challenge!

The goal is to reach a target net worth within a set number of turns without going bankrupt yourself.

## Features

*   **Core Business Mechanics:** Production, Pricing, Marketing, R&D.
*   **Staffing Management:** Hire/fire workers, manage salaries, production limited by workforce capacity.
*   **Dynamic Market:** Demand fluctuates based on price, quality, marketing, trends, and random events.
*   **AI Competition:** Features a single AI opponent with its own strategy and financial tracking.
*   **AI Respawn:** Bankrupt AI competitors are replaced by new ones.
*   **Loan System:** Take out and repay loans, manage interest payments. Interest accrues on the balance *before* repayments are applied for the turn.
*   **R&D Progression:** Invest points to earn breakthroughs; choose between improving quality or reducing production costs.
*   **Turn-Based Gameplay:** Clear decision phase and processing phase each "month".
*   **Detailed Financial Reporting:** End-of-turn summaries display Revenue, COGS, Expenses (Salaries, Marketing, R&D, Interest, Hiring/Firing), Loan Repayments, and Net Income for both the player and the AI.
*   **Save/Load Functionality:** Persist game state between sessions using Python's `pickle` module (saves to `business_sim_save.pkl`).
*   **Configurable Parameters:** Easily tweak game difficulty, pacing, and economic factors via constants at the top of the script.
*   **Text-Based Interface:** Runs directly in your terminal.

## How to Play/Run

1.  **Prerequisites:**
    *   Python 3 installed (version 3.6+ recommended for f-string support).

2.  **Get the Code:**
    *   Clone this repository:
        ```bash
        git clone <repository_url>
        cd <repository_directory>
        ```
    *   Or download the `business_sim.py` (or your script's name) file directly.

3.  **Run the Game:**
    *   Open your terminal or command prompt.
    *   Navigate to the directory containing the script.
    *   Execute the script using Python 3:
        ```bash
        python3 business_sim.py
        ```
        *(Use `python` instead of `python3` if `python` is linked to your Python 3 installation).*

4.  **Load Save (Optional):**
    *   If a `business_sim_save.pkl` file exists in the same directory, the game will prompt you to load the saved game.

5.  **Follow Prompts:**
    *   Each turn, the game will display your current status and the competitor's estimated status.
    *   You will be prompted to make decisions regarding:
        *   Hiring/Firing workers
        *   Production quantity
        *   Unit price
        *   Marketing investment (to increase level)
        *   R&D investment (to gain points)
        *   Taking/Repaying loans
    *   You can choose to save the game before the turn is processed.

6.  **Goal:**
    *   Reach the `TARGET_NET_WORTH` specified in the configuration before the `MAX_TURNS` limit is reached.
    *   Avoid bankruptcy (negative net worth and negative cash).

## Configuration / Tweaking

The gameplay difficulty, pacing, and economic environment can be easily modified by changing the constant values defined in the **`# --- Configuration ---`** section near the top of the Python script (`business_sim.py`).

Key variables include:

*   `INITIAL_MONEY`, `TARGET_NET_WORTH`, `MAX_TURNS`: Game start/end conditions.
*   `BASE_DEMAND`, `*_SENSITIVITY`, `COMPETITION_SENSITIVITY`: Market behaviour.
*   `INITIAL_PROD_COST`, `INITIAL_QUALITY`, `INITIAL_MARKETING_LVL`: Starting product stats.
*   `WORKER_SALARY`, `MAX_PROD_PER_WORKER`, `HIRING_COST_PER_WORKER`, `FIRING_COST_PER_WORKER`: Staffing costs and efficiency.
*   `RND_COST_FACTOR`, `RND_POINTS_PER_UPGRADE`, `MARKETING_COST_FACTOR`: Investment costs.
*   `INTEREST_RATE`, `LOAN_INTEREST_RATE`, `MAX_LOAN_RATIO`: Financial parameters.

Feel free to experiment with these values to create different gameplay challenges!

## Technologies Used

*   Python 3

## Potential Future Enhancements

*   Multiple AI competitors.
*   Multiple product lines research/launch.
*   More complex events with player choices.
*   More sophisticated debt financing options.
*   Stock Market / Company Valuation mechanics.
*   Graphical User Interface (GUI).