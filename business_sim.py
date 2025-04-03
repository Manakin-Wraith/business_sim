import random
import time
import math

# --- Configuration ---
INITIAL_MONEY = 10000
TARGET_NET_WORTH = 100000
MAX_TURNS = 24 # Represents 2 years (months)

BASE_DEMAND = 100
DEMAND_PRICE_SENSITIVITY = 1.5 # Higher means price matters more
DEMAND_QUALITY_SENSITIVITY = 1.2 # Higher means quality matters more
DEMAND_MARKETING_SENSITIVITY = 1.0 # Higher means marketing matters more

INITIAL_PROD_COST = 15
INITIAL_QUALITY = 3 # Scale of 1-10
INITIAL_MARKETING_LVL = 1 # Scale of 1-10

RND_COST_FACTOR = 500  # Cost per point increases with quality/cost reduction
RND_POINTS_PER_UPGRADE = 100
MARKETING_COST_FACTOR = 300 # Cost per point increases with level

INTEREST_RATE = 0.05 # Annual interest on cash reserves (paid monthly)
LOAN_INTEREST_RATE = 0.10 # Annual interest on loans (paid monthly)
MAX_LOAN_RATIO = 2.0 # Max loan amount relative to current assets (money + inventory value)

# --- Helper Functions ---
def format_currency(amount):
    """Formats a number as currency."""
    return "${:,.2f}".format(amount)

def get_int_input(prompt, min_val=None, max_val=None):
    """Gets validated integer input from the user."""
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(f"Value must be at least {min_val}.")
            elif max_val is not None and value > max_val:
                print(f"Value must be no more than {max_val}.")
            else:
                return value
        except ValueError:
            print("Invalid input. Please enter a whole number.")

def display_bar(label, value, max_value, length=20):
    """Displays a simple text-based progress bar."""
    filled_length = int(length * value / max_value)
    bar = '█' * filled_length + '-' * (length - filled_length)
    return f"{label:<12} [{bar}] {value}/{max_value}"

# --- Game Classes ---
class Business:
    """Represents the player's business state."""
    def __init__(self):
        self.money = INITIAL_MONEY
        self.inventory = 0
        self.production_cost = INITIAL_PROD_COST
        self.product_quality = INITIAL_QUALITY # 1-10
        self.marketing_level = INITIAL_MARKETING_LVL # 1-10
        self.price_per_unit = self.production_cost * 2 # Initial pricing guess
        self.rnd_points = 0
        self.loan_amount = 0
        self.last_turn_sales = 0
        self.last_turn_profit = 0
        self.total_profit = 0

    def calculate_net_worth(self):
        """Calculates current net worth (Assets - Liabilities)."""
        inventory_value = self.inventory * self.production_cost # Value at cost
        assets = self.money + inventory_value
        liabilities = self.loan_amount
        return assets - liabilities

    def get_max_loan(self):
        """Calculates the maximum loan amount allowed."""
        assets = self.money + (self.inventory * self.production_cost)
        return max(0, (assets * MAX_LOAN_RATIO) - self.loan_amount)

    def apply_interest(self):
        """Applies interest to cash reserves and loans."""
        # Interest earned on cash (if positive balance)
        if self.money > 0:
            interest_earned = self.money * (INTEREST_RATE / 12)
            self.money += interest_earned
            # print(f"  Interest earned: {format_currency(interest_earned)}") # Optional detail

        # Interest paid on loan
        if self.loan_amount > 0:
            interest_paid = self.loan_amount * (LOAN_INTEREST_RATE / 12)
            self.money -= interest_paid
            # print(f"  Loan interest paid: {format_currency(interest_paid)}") # Optional detail
            if self.money < 0:
                print("  WARNING: Loan interest payment resulted in negative cash!")


class Market:
    """Represents the market dynamics."""
    def __init__(self):
        self.current_base_demand = BASE_DEMAND
        self.trend = 1.0 # Multiplier for demand (e.g., 1.1 = growing, 0.9 = shrinking)
        self.last_event = "No significant market events."

    def update_trend(self):
        """Slightly adjusts the market trend randomly."""
        change = random.uniform(-0.05, 0.05)
        self.trend = max(0.5, min(1.5, self.trend + change)) # Keep trend within bounds

    def calculate_demand(self, price, quality, marketing_lvl):
        """Calculates estimated demand for the turn."""
        # Price effect: Higher price reduces demand more sharply
        # Avoid division by zero; ensure price > 0
        safe_price = max(1, price)
        price_factor = (INITIAL_PROD_COST * 2 / safe_price) ** DEMAND_PRICE_SENSITIVITY

        # Quality effect: Higher quality increases demand
        quality_factor = (quality / 5.0) ** DEMAND_QUALITY_SENSITIVITY # Normalized around 5

        # Marketing effect: Higher marketing increases demand
        marketing_factor = (marketing_lvl / 5.0) ** DEMAND_MARKETING_SENSITIVITY # Normalized around 5

        # Combine factors with base demand and trend
        demand = self.current_base_demand * self.trend * price_factor * quality_factor * marketing_factor

        # Add some randomness
        demand *= random.uniform(0.9, 1.1)

        return max(0, int(demand)) # Ensure demand is not negative

    def generate_event(self, business):
        """Generates a random market event."""
        self.last_event = "No significant market events."
        roll = random.random() # 0.0 to 1.0

        if roll < 0.1: # Negative Event (10% chance)
            event_type = random.choice(['RECESSION', 'COMPETITOR', 'SUPPLY_ISSUE'])
            if event_type == 'RECESSION' and self.trend > 0.7:
                self.trend *= random.uniform(0.7, 0.9)
                self.last_event = "Economic downturn! Market demand trend has decreased."
            elif event_type == 'COMPETITOR':
                self.current_base_demand *= random.uniform(0.8, 0.95)
                self.last_event = "A new competitor heats up the market! Base demand slightly lower."
            elif event_type == 'SUPPLY_ISSUE':
                cost_increase = random.uniform(1.05, 1.20)
                business.production_cost *= cost_increase
                self.last_event = f"Supply chain disruption! Production costs increased by {((cost_increase-1)*100):.1f}%."

        elif roll > 0.9: # Positive Event (10% chance)
            event_type = random.choice(['BOOM', 'POSITIVE_PR', 'TECH_BREAKTHROUGH'])
            if event_type == 'BOOM' and self.trend < 1.3:
                self.trend *= random.uniform(1.1, 1.3)
                self.last_event = "Economic boom! Market demand trend has increased."
            elif event_type == 'POSITIVE_PR':
                business.marketing_level = min(10, business.marketing_level + random.randint(1, 2))
                self.last_event = "Positive PR! Your product gained unexpected attention (Marketing Level up!)."
            elif event_type == 'TECH_BREAKTHROUGH':
                 # Give some free R&D points
                 points = random.randint(20, 50)
                 business.rnd_points += points
                 self.last_event = f"Industry technology breakthrough assists your R&D! (+{points} R&D points)."
        # Else (80% chance): No significant event


class Game:
    """Manages the game state and loop."""
    def __init__(self):
        self.business = Business()
        self.market = Market()
        self.turn = 1

    def print_status(self):
        """Prints the current game status."""
        print("\n" + "="*40)
        print(f"Turn: {self.turn} / {MAX_TURNS}")
        print(f"Goal: Reach {format_currency(TARGET_NET_WORTH)} Net Worth")
        print(f"Current Net Worth: {format_currency(self.business.calculate_net_worth())}")
        print("-"*40)
        print(f"Cash: {format_currency(self.business.money)}")
        print(f"Loan Amount: {format_currency(self.business.loan_amount)}")
        print(f"Inventory: {self.business.inventory} units")
        print(f"Price per Unit: {format_currency(self.business.price_per_unit)}")
        print(f"Production Cost per Unit: {format_currency(self.business.production_cost)}")
        print(display_bar("Quality", self.business.product_quality, 10))
        print(display_bar("Marketing", self.business.marketing_level, 10))
        print(f"R&D Progress: {self.business.rnd_points} / {RND_POINTS_PER_UPGRADE} points")
        print("-"*40)
        print(f"Last Turn Sales: {self.business.last_turn_sales} units")
        print(f"Last Turn Profit: {format_currency(self.business.last_turn_profit)}")
        print(f"Total Profit: {format_currency(self.business.total_profit)}")
        print(f"Market Event: {self.market.last_event}")
        print(f"Market Trend: {self.market.trend:.2f} (Demand Multiplier)")
        print("="*40 + "\n")

    def get_player_actions(self):
        """Gets the player's decisions for the turn."""
        print("--- Decisions for Turn {} ---".format(self.turn))

        # 1. Production
        max_affordable = int(self.business.money // self.business.production_cost) if self.business.production_cost > 0 else 0
        print(f"You can afford to produce up to {max_affordable} units (Cost: {format_currency(self.business.production_cost)} each).")
        produce_units = get_int_input(f"How many units to produce? (Current Inv: {self.business.inventory}) ", 0, max_affordable)
        cost_to_produce = produce_units * self.business.production_cost
        self.business.money -= cost_to_produce
        self.business.inventory += produce_units
        print(f"Produced {produce_units} units. Cost: {format_currency(cost_to_produce)}. Cash remaining: {format_currency(self.business.money)}")

        # 2. Pricing
        print(f"\nCurrent price: {format_currency(self.business.price_per_unit)}")
        new_price = get_int_input("Set new price per unit: $", 1) # Price must be at least $1
        self.business.price_per_unit = new_price

        # 3. Marketing Investment
        current_marketing_cost = int(MARKETING_COST_FACTOR * (self.business.marketing_level ** 1.5)) # Increasing cost
        print(f"\nCurrent Marketing Level: {self.business.marketing_level}/10")
        print(f"Cost to increase Marketing Level by 1: ~{format_currency(current_marketing_cost)}")
        max_affordable_marketing = int(self.business.money)
        invest_marketing = get_int_input(f"How much to invest in Marketing? (Max: {format_currency(max_affordable_marketing)}) $", 0, max_affordable_marketing)
        if invest_marketing > 0 and self.business.marketing_level < 10:
             # Simple incremental increase for now, could be points-based
             levels_gained = math.sqrt(invest_marketing / MARKETING_COST_FACTOR) # Non-linear gain
             # More realistic: use points or diminishing returns
             if invest_marketing >= current_marketing_cost:
                 self.business.marketing_level = min(10, self.business.marketing_level + 1)
                 actual_cost = current_marketing_cost # Charge the cost for the level increase
                 self.business.money -= actual_cost
                 print(f"Marketing level increased to {self.business.marketing_level}! Cost: {format_currency(actual_cost)}")
             else:
                 # Maybe add partial progress later? For now, must meet threshold.
                 print(f"Investment of {format_currency(invest_marketing)} is not enough to increase marketing level (requires ~{format_currency(current_marketing_cost)}).")
                 # Refund if you want, or consider it spent on minor efforts
                 # self.business.money += invest_marketing # Refund example
                 pass # Or just let the money be spent inefficiently
        elif self.business.marketing_level >= 10:
            print("Marketing is already at maximum level (10).")
        self.business.money -= invest_marketing # Deduct investment even if level doesn't increase (represents spending)


        # 4. R&D Investment
        current_rnd_cost = int(RND_COST_FACTOR * (self.business.product_quality + (20 - self.business.production_cost))) # Cost increases with progress
        print(f"\nCurrent Quality: {self.business.product_quality}/10, Prod Cost: {format_currency(self.business.production_cost)}")
        print(f"R&D Progress: {self.business.rnd_points}/{RND_POINTS_PER_UPGRADE}")
        print(f"Cost per R&D point: ~${current_rnd_cost / 100:.2f} (Estimate)") # Rough estimate
        max_affordable_rnd = int(self.business.money)
        invest_rnd = get_int_input(f"How much to invest in R&D? (Max: {format_currency(max_affordable_rnd)}) $", 0, max_affordable_rnd)
        if invest_rnd > 0:
            points_gained = int(invest_rnd / (current_rnd_cost / RND_POINTS_PER_UPGRADE + 1)) # +1 to avoid div by zero, rough calc
            self.business.rnd_points += points_gained
            self.business.money -= invest_rnd
            print(f"Invested {format_currency(invest_rnd)} in R&D, gained approx {points_gained} points.")

            # Check for R&D breakthroughs
            while self.business.rnd_points >= RND_POINTS_PER_UPGRADE:
                self.business.rnd_points -= RND_POINTS_PER_UPGRADE
                # Choose upgrade: bias towards quality if cost is low, vice versa
                upgrade_choice = random.random()
                quality_cap = self.business.product_quality >= 10
                cost_floor = self.business.production_cost <= 5 # Min production cost

                if quality_cap and cost_floor:
                    print("R&D Breakthrough! But Quality and Production Cost are already maxed/minned.")
                    self.business.rnd_points = 0 # Reset points if nothing to improve
                    break
                elif quality_cap:
                     upgrade_choice = 1.0 # Force cost reduction
                elif cost_floor:
                     upgrade_choice = 0.0 # Force quality improvement


                if upgrade_choice < 0.6: # 60% chance to improve quality (if not capped)
                   if not quality_cap:
                        self.business.product_quality += 1
                        print("R&D Breakthrough! Product Quality increased to {}!".format(self.business.product_quality))
                   else: # Should not happen due to check above, but safeguard
                        if not cost_floor:
                             self.business.production_cost = max(5, self.business.production_cost - random.randint(1, 3))
                             print(f"R&D Breakthrough! Production Cost reduced to {format_currency(self.business.production_cost)}!")
                else: # 40% chance to reduce production cost (if not floored)
                    if not cost_floor:
                        self.business.production_cost = max(5, self.business.production_cost - random.randint(1, 3)) # Reduce by 1-3 dollars
                        print(f"R&D Breakthrough! Production Cost reduced to {format_currency(self.business.production_cost)}!")
                    else: # Safeguard
                         if not quality_cap:
                            self.business.product_quality += 1
                            print("R&D Breakthrough! Product Quality increased to {}!".format(self.business.product_quality))

        # 5. Loan Management
        print(f"\nCurrent Loan: {format_currency(self.business.loan_amount)}")
        max_loan = self.business.get_max_loan()
        print(f"Maximum additional loan available: {format_currency(max_loan)}")
        take_loan = get_int_input(f"How much new loan to take? (Enter 0 for none) $", 0, int(max_loan))
        if take_loan > 0:
            self.business.loan_amount += take_loan
            self.business.money += take_loan
            print(f"Took out loan of {format_currency(take_loan)}. Total loan: {format_currency(self.business.loan_amount)}. Cash: {format_currency(self.business.money)}")

        max_repayment = min(self.business.loan_amount, self.business.money)
        if self.business.loan_amount > 0:
            repay_loan = get_int_input(f"How much loan to repay? (Max: {format_currency(max_repayment)}) $", 0, int(max_repayment))
            if repay_loan > 0:
                self.business.loan_amount -= repay_loan
                self.business.money -= repay_loan
                print(f"Repaid {format_currency(repay_loan)} of loan. Remaining loan: {format_currency(self.business.loan_amount)}. Cash: {format_currency(self.business.money)}")


    def process_turn(self):
        """Simulates the market and updates business state."""
        print("\n--- Processing Turn {} ---".format(self.turn))
        time.sleep(1) # Pause for effect

        # 1. Market Simulation
        self.market.update_trend()
        self.market.generate_event(self.business) # Events might change costs, marketing etc. before sales calc

        demand = self.market.calculate_demand(
            self.business.price_per_unit,
            self.business.product_quality,
            self.business.marketing_level
        )
        print(f"Market Analysis: Estimated demand this turn is {demand} units.")

        # 2. Sales Calculation
        units_sold = min(self.business.inventory, demand)
        if units_sold > 0:
            revenue = units_sold * self.business.price_per_unit
            cost_of_goods_sold = units_sold * self.business.production_cost # Use current prod cost
            profit = revenue - cost_of_goods_sold

            self.business.inventory -= units_sold
            self.business.money += revenue
            self.business.last_turn_sales = units_sold
            self.business.last_turn_profit = profit
            self.business.total_profit += profit

            print(f"Sales: Sold {units_sold} units at {format_currency(self.business.price_per_unit)} each.")
            print(f"Revenue: {format_currency(revenue)}")
            print(f"Cost of Goods Sold: {format_currency(cost_of_goods_sold)}")
            print(f"Gross Profit this turn: {format_currency(profit)}")
        else:
            print("Sales: No units sold this turn.")
            self.business.last_turn_sales = 0
            self.business.last_turn_profit = 0 # No sales, no profit from sales

        # 3. Apply Interest (after sales, before checking bankruptcy)
        self.business.apply_interest()
        print(f"Cash after sales and interest: {format_currency(self.business.money)}")


        # 4. Advance Turn Counter
        self.turn += 1


    def check_game_over(self):
        """Checks for win/loss conditions."""
        net_worth = self.business.calculate_net_worth()

        # Loss Condition 1: Bankruptcy (Negative Net Worth)
        # Using net worth is more robust than just cash < 0, as inventory/loans matter
        if net_worth < 0:
            print("\n" + "#"*40)
            print("             GAME OVER - BANKRUPTCY!")
            print(f"Your company's net worth dropped below zero ({format_currency(net_worth)}).")
            print(f"You survived {self.turn -1} turns.")
            print(f"Total Profit achieved: {format_currency(self.business.total_profit)}")
            print("#"*40)
            return True

        # Loss Condition 2: Ran out of time
        if self.turn > MAX_TURNS:
            print("\n" + "#"*40)
            print("              GAME OVER - OUT OF TIME!")
            print(f"You completed {MAX_TURNS} turns.")
            print(f"Final Net Worth: {format_currency(net_worth)}")
            if net_worth >= TARGET_NET_WORTH:
                 print("However, you achieved the target net worth! Well done!")
                 print("             -- YOU WIN! (Time Limit Victory) --")
            else:
                 print(f"Target Net Worth ({format_currency(TARGET_NET_WORTH)}) was not reached.")
                 print("             -- YOU LOST --")

            print(f"Total Profit achieved: {format_currency(self.business.total_profit)}")
            print("#"*40)
            return True

        # Win Condition: Reached target net worth
        if net_worth >= TARGET_NET_WORTH:
            print("\n" + "*"*40)
            print("         CONGRATULATIONS - YOU WIN!")
            print(f"You reached the target net worth of {format_currency(TARGET_NET_WORTH)}!")
            print(f"Final Net Worth: {format_currency(net_worth)}")
            print(f"Achieved in {self.turn -1} turns.")
            print(f"Total Profit: {format_currency(self.business.total_profit)}")
            print("*"*40)
            return True

        # Loss Condition 3: Stagnation (Optional - harder to implement well)
        # e.g., if money is near zero and no inventory for several turns.

        return False

    def run(self):
        """Main game loop."""
        print("Welcome to Business Tycoon Simulator!")
        print(f"Your goal is to reach a net worth of {format_currency(TARGET_NET_WORTH)} in {MAX_TURNS} months.")
        print("Good luck!")

        while True:
            self.print_status()
            if self.check_game_over():
                break
            self.get_player_actions()
            self.process_turn()
            # Small delay to make turns feel distinct
            # time.sleep(0.5)

        print("\nThank you for playing!")

# --- Run the Game ---
if __name__ == "__main__":
    game = Game()
    game.run()