import random
import time
import math
import pickle # For saving/loading
import os # For checking if save file exists

# --- Configuration ---
INITIAL_MONEY = 10000
TARGET_NET_WORTH = 150000 # Increased goal for more challenge
MAX_TURNS = 36 # Represents 3 years (months)

BASE_DEMAND = 150 # Slightly higher base demand due to competition splitting it
DEMAND_PRICE_SENSITIVITY = 1.6 # How much price affects demand
DEMAND_QUALITY_SENSITIVITY = 1.3 # How much quality affects demand
DEMAND_MARKETING_SENSITIVITY = 1.1 # How much marketing affects demand
COMPETITION_SENSITIVITY = 0.7 # How much competitor stats affect your share (0=no effect, 1=high effect)

INITIAL_PROD_COST = 18
INITIAL_QUALITY = 3 # Scale of 1-10
INITIAL_MARKETING_LVL = 1 # Scale of 1-10

INITIAL_WORKERS = 5
WORKER_SALARY = 150 # Monthly salary per worker
MAX_PROD_PER_WORKER = 10 # Units per worker per month
HIRING_COST_PER_WORKER = 250 # One-time cost to hire
FIRING_COST_PER_WORKER = 500 # One-time cost to fire (severance etc)

RND_COST_FACTOR = 600
RND_POINTS_PER_UPGRADE = 120
MARKETING_COST_FACTOR = 400

INTEREST_RATE = 0.05 # Annual interest on cash reserves (paid monthly)
LOAN_INTEREST_RATE = 0.10 # Annual interest on loans (paid monthly)
MAX_LOAN_RATIO = 2.0 # Max loan amount relative to current assets

SAVE_FILENAME = "business_sim_save.pkl"

# --- Helper Functions ---
def format_currency(amount):
    """Formats a number as currency."""
    return "${:,.2f}".format(amount)

def get_int_input(prompt, min_val=None, max_val=None):
    """Gets validated integer input from the user."""
    while True:
        try:
            value_str = input(prompt).strip()
            if not value_str: # Handle empty input
                 if min_val is not None and 0 < min_val:
                     print(f"Input cannot be empty. Please enter a number.")
                     continue
                 else:
                     value = 0 # Default to 0 if allowed
            else:
                value = int(value_str)

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
    value = max(0, min(value, max_value)) # Clamp value
    filled_length = int(length * value / max_value)
    bar = '█' * filled_length + '-' * (length - filled_length)
    return f"{label:<12} [{bar}] {value}/{max_value}"

# --- Game Classes ---

class Business:
    """Represents the state of a business (Player or AI)."""
    def __init__(self, name="Player", is_ai=False, initial_money=INITIAL_MONEY):
        self.name = name
        self.is_ai = is_ai
        self.money = initial_money
        self.inventory = 0
        self.production_cost = INITIAL_PROD_COST
        self.product_quality = INITIAL_QUALITY # 1-10
        self.marketing_level = INITIAL_MARKETING_LVL # 1-10
        self.price_per_unit = self.production_cost * 2.5 # Start a bit higher
        self.rnd_points = 0
        self.loan_amount = 0
        self.last_turn_sales = 0
        self.last_turn_profit = 0
        self.total_profit = 0
        self.workers = INITIAL_WORKERS
        self.bankrupt = False # Flag if bankrupt

    @property
    def max_production_capacity(self):
        """Calculates max production based on workers."""
        return self.workers * MAX_PROD_PER_WORKER

    def calculate_assets(self):
        """Calculate total assets (cash + inventory value)."""
        inventory_value = self.inventory * self.production_cost # Value at cost
        return self.money + inventory_value

    def calculate_net_worth(self):
        """Calculates current net worth (Assets - Liabilities)."""
        assets = self.calculate_assets()
        liabilities = self.loan_amount
        return assets - liabilities

    def get_max_loan(self):
        """Calculates the maximum loan amount allowed."""
        assets = self.calculate_assets()
        # Allow loan even if assets are slightly negative, maybe up to 0?
        return max(0, (assets * MAX_LOAN_RATIO) - self.loan_amount)

    def apply_interest_and_salaries(self):
        """Applies interest to cash/loans and deducts salaries."""
        # Salaries
        salary_cost = self.workers * WORKER_SALARY
        self.money -= salary_cost
        # print(f"  {self.name} Salaries paid: {format_currency(salary_cost)}") # Optional detail

        # Interest earned on cash (if positive balance)
        interest_earned = 0
        if self.money > 0:
            interest_earned = self.money * (INTEREST_RATE / 12)
            self.money += interest_earned
            # print(f"  {self.name} Interest earned: {format_currency(interest_earned)}") # Optional detail

        # Interest paid on loan
        interest_paid = 0
        if self.loan_amount > 0:
            interest_paid = self.loan_amount * (LOAN_INTEREST_RATE / 12)
            self.money -= interest_paid
            # print(f"  {self.name} Loan interest paid: {format_currency(interest_paid)}") # Optional detail

        return salary_cost, interest_earned, interest_paid

    def process_sales(self, units_sold):
        """Updates state after sales."""
        if units_sold > 0 and units_sold <= self.inventory:
            revenue = units_sold * self.price_per_unit
            cost_of_goods_sold = units_sold * self.production_cost
            profit = revenue - cost_of_goods_sold

            self.inventory -= units_sold
            self.money += revenue
            self.last_turn_sales = units_sold
            self.last_turn_profit = profit
            self.total_profit += profit
            return revenue, cost_of_goods_sold, profit
        else:
            self.last_turn_sales = 0
            self.last_turn_profit = 0
            return 0, 0, 0

    def check_bankruptcy(self):
        if self.calculate_net_worth() < 0 and self.money < 0:
             # Stricter: Negative net worth AND negative cash
            self.bankrupt = True
            return True
        return False


class AI_Business(Business):
    """Represents an AI controlled business."""
    def __init__(self, name="Competitor", difficulty=0.5): # difficulty 0-1
        super().__init__(name=name, is_ai=True, initial_money=INITIAL_MONEY * 0.9) # Start slightly poorer
        self.difficulty = difficulty # Influences decision making aggression/smarts
        self.target_inventory_ratio = 1.5 # Try to keep 1.5x last month's sales in stock
        self.investment_aggressiveness = 0.1 + (difficulty * 0.2) # % of cash to consider for inv.
        self.pricing_margin = 1.5 + (random.uniform(-0.2, 0.4) * (1+difficulty)) # Target margin over cost


    def make_decisions(self, market_trend, player_business):
        """AI makes decisions for the turn."""
        if self.bankrupt: return

        # --- 1. Production ---
        # Target inventory based on last sales and market trend prediction
        predicted_demand = self.last_turn_sales * market_trend * random.uniform(0.8, 1.2)
        target_inventory = int(predicted_demand * self.target_inventory_ratio)
        needed_production = max(0, target_inventory - self.inventory)
        affordable_production = int(self.money // self.production_cost) if self.production_cost > 0 else 0
        produce_units = min(needed_production, self.max_production_capacity, affordable_production)

        # Basic check: Don't spend *all* money on production if low
        if produce_units * self.production_cost > self.money * 0.7:
             produce_units = int((self.money * 0.7) // self.production_cost) if self.production_cost > 0 else 0

        produce_units = max(0, produce_units) # Ensure non-negative

        cost_to_produce = produce_units * self.production_cost
        self.money -= cost_to_produce
        self.inventory += produce_units

        # --- 2. Pricing ---
        # Adjust pricing based on costs, inventory levels, and player price (simple reaction)
        base_price = self.production_cost * self.pricing_margin
        # If inventory is high, lower price slightly
        if self.inventory > target_inventory * 1.5:
            base_price *= random.uniform(0.9, 0.98)
        # If inventory is low, raise price slightly
        elif self.inventory < target_inventory * 0.5 and self.inventory > 0:
            base_price *= random.uniform(1.02, 1.1)

        # React slightly to player price (more reaction with higher difficulty)
        price_diff_factor = 1.0 + (player_business.price_per_unit - base_price) / base_price * (self.difficulty * 0.2)
        self.price_per_unit = max(self.production_cost + 1, int(base_price * price_diff_factor)) # Ensure price > cost

        # --- 3. Staffing ---
        needed_workers = math.ceil(needed_production / MAX_PROD_PER_WORKER) if MAX_PROD_PER_WORKER > 0 else self.workers
        target_workers = max(1, needed_workers + random.randint(-1, 2)) # Add some buffer/randomness

        # Only hire/fire if significantly different and affordable
        if target_workers > self.workers and self.money > (HIRING_COST_PER_WORKER * (target_workers - self.workers) + WORKER_SALARY * target_workers):
            workers_to_hire = target_workers - self.workers
            hire_cost = workers_to_hire * HIRING_COST_PER_WORKER
            if self.money > hire_cost + 5000: # Keep buffer
                self.money -= hire_cost
                self.workers += workers_to_hire
        elif target_workers < self.workers and (self.workers - target_workers) >= 2: # Only fire if difference is 2+
             workers_to_fire = self.workers - target_workers
             fire_cost = workers_to_fire * FIRING_COST_PER_WORKER
             if self.money > fire_cost + 2000: # Keep buffer even when firing
                 self.money -= fire_cost
                 self.workers -= workers_to_fire
             elif self.money < 1000 : # Desperate measures
                 self.workers -= workers_to_fire # Fire anyway if cash is super low, ignore cost for simplicity here


        # --- 4. Marketing & R&D ---
        # Simple investment strategy: invest a portion of cash if above a threshold
        investment_budget = self.money * self.investment_aggressiveness
        if self.money > 5000 and investment_budget > 500:
            marketing_investment = investment_budget * 0.6 * random.uniform(0.5, 1.5)
            rnd_investment = investment_budget * 0.4 * random.uniform(0.5, 1.5)

            # Marketing
            current_marketing_cost = int(MARKETING_COST_FACTOR * (self.marketing_level ** 1.5))
            if self.marketing_level < 10 and marketing_investment >= current_marketing_cost and self.money > marketing_investment + 2000:
                 self.money -= current_marketing_cost
                 self.marketing_level += 1
                 # print(f"Debug AI: {self.name} increased Marketing to {self.marketing_level}") # Debug

            # R&D
            current_rnd_cost_per_point = RND_COST_FACTOR * (self.product_quality + (20 - self.production_cost)) / RND_POINTS_PER_UPGRADE + 1
            if rnd_investment > 0 and self.money > rnd_investment + 2000:
                points_gained = int(rnd_investment / current_rnd_cost_per_point)
                self.money -= rnd_investment
                self.rnd_points += points_gained

                # AI R&D breakthroughs (simpler than player's choice)
                while self.rnd_points >= RND_POINTS_PER_UPGRADE:
                    self.rnd_points -= RND_POINTS_PER_UPGRADE
                    if self.product_quality >= 10 and self.production_cost <= 5: break # Maxed out

                    # Slightly biased towards quality initially, then cost reduction
                    improve_quality_chance = 0.6 if self.product_quality < 7 else 0.3
                    if random.random() < improve_quality_chance and self.product_quality < 10:
                        self.product_quality += 1
                        # print(f"Debug AI: {self.name} increased Quality to {self.product_quality}") # Debug
                    elif self.production_cost > 5:
                        self.production_cost = max(5, self.production_cost - random.randint(1, 2))
                        # print(f"Debug AI: {self.name} reduced Prod Cost to {self.production_cost}") # Debug
                    elif self.product_quality < 10: # Fallback if cost reduction failed/capped
                         self.product_quality += 1
                         # print(f"Debug AI: {self.name} increased Quality to {self.product_quality}") # Debug

        # --- 5. Loans (Very Simple AI Logic) ---
        # Take loan if cash is critically low for production/salaries
        estimated_expenses = (self.workers * WORKER_SALARY) + (needed_production * self.production_cost * 0.5) # Rough estimate
        if self.money < estimated_expenses and self.get_max_loan() > 1000:
             loan_needed = max(1000, estimated_expenses - self.money)
             loan_to_take = min(loan_needed, self.get_max_loan())
             self.loan_amount += loan_to_take
             self.money += loan_to_take
             # print(f"Debug AI: {self.name} took loan {loan_to_take}") # Debug

        # Repay loan if cash is very high
        elif self.loan_amount > 0 and self.money > self.loan_amount * 2 + 20000: # Have lots of spare cash
             repay_amount = min(self.loan_amount, self.money - 10000) # Keep a buffer
             self.loan_amount -= repay_amount
             self.money -= repay_amount
             # print(f"Debug AI: {self.name} repaid loan {repay_amount}") # Debug


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

    def calculate_total_potential_demand(self, businesses):
        """Calculates the total market demand potential before splitting."""
        # Use average price, quality, marketing as a baseline indicator? Or player's?
        # Let's use player's stats primarily, adjusted by market trend.
        # This assumes player is the main focus, market reacts 'around' them.
        player = businesses[0] # Assume player is the first element

        safe_price = max(1, player.price_per_unit)
        price_factor = (INITIAL_PROD_COST * 2 / safe_price) ** DEMAND_PRICE_SENSITIVITY
        quality_factor = (player.product_quality / 5.0) ** DEMAND_QUALITY_SENSITIVITY
        marketing_factor = (player.marketing_level / 5.0) ** DEMAND_MARKETING_SENSITIVITY

        # Basic demand influenced by player stats and overall trend
        demand = self.current_base_demand * self.trend * price_factor * quality_factor * marketing_factor
        demand *= random.uniform(0.9, 1.1) # Add noise

        return max(0, int(demand))

    def calculate_market_shares(self, businesses, total_demand):
        """Splits the total demand among businesses based on competitiveness."""
        scores = {}
        total_score = 0

        for biz in businesses:
            if biz.bankrupt or biz.inventory == 0: # Bankrupt or no inventory = no sales
                scores[biz.name] = 0
                continue

            # Calculate a competitiveness score (higher is better)
            # Price: Lower is better (inverse relationship)
            price_score = (1 / max(1, biz.price_per_unit)) ** (DEMAND_PRICE_SENSITIVITY * COMPETITION_SENSITIVITY)
            # Quality: Higher is better
            quality_score = biz.product_quality ** (DEMAND_QUALITY_SENSITIVITY * COMPETITION_SENSITIVITY)
            # Marketing: Higher is better
            marketing_score = biz.marketing_level ** (DEMAND_MARKETING_SENSITIVITY * COMPETITION_SENSITIVITY)

            # Combine scores (multiplicative) - adjust exponents to tune sensitivity
            score = price_score * quality_score * marketing_score * random.uniform(0.95, 1.05) # Small random factor per company
            scores[biz.name] = score
            total_score += score

        sales = {}
        if total_score == 0: # If no one can sell, zero sales for all
            for biz in businesses:
                sales[biz.name] = 0
        else:
            remaining_demand = total_demand
            sorted_businesses = sorted(businesses, key=lambda b: scores[b.name], reverse=True) # Prioritize higher scores

            for i, biz in enumerate(sorted_businesses):
                 if biz.bankrupt or remaining_demand <= 0 :
                     sales[biz.name] = 0
                     continue

                 share_ratio = scores[biz.name] / total_score if total_score > 0 else 0
                 potential_sales = math.ceil(total_demand * share_ratio) # Theoretical share

                 # Cannot sell more than inventory or remaining demand
                 actual_sales = min(biz.inventory, potential_sales, remaining_demand)
                 sales[biz.name] = actual_sales
                 remaining_demand -= actual_sales


            # Address potential rounding issues / edge cases if demand wasn't fully met
            # but someone still had inventory and score. This basic model assumes
            # higher scores get first dibs up to their potential share.

        return sales


    def generate_event(self, businesses):
        """Generates a random market event, potentially affecting all businesses."""
        self.last_event = "No significant market events."
        roll = random.random()

        if roll < 0.15: # Negative Event (15% chance)
            event_type = random.choice(['RECESSION', 'SUPPLY_ISSUE', 'WAGE_HIKE'])
            if event_type == 'RECESSION' and self.trend > 0.7:
                self.trend *= random.uniform(0.7, 0.9)
                self.last_event = "Economic downturn! Market demand trend has decreased."
            elif event_type == 'SUPPLY_ISSUE':
                cost_increase = random.uniform(1.05, 1.20)
                affected_biz_count = 0
                for biz in businesses:
                     if not biz.bankrupt:
                        biz.production_cost *= cost_increase
                        affected_biz_count += 1
                self.last_event = f"Supply chain disruption! Production costs increased by {((cost_increase-1)*100):.1f}% for {affected_biz_count} businesses."
            elif event_type == 'WAGE_HIKE':
                 global WORKER_SALARY # Need global to modify config variable
                 old_salary = WORKER_SALARY
                 WORKER_SALARY = int(WORKER_SALARY * random.uniform(1.1, 1.25))
                 self.last_event = f"Industry-wide wage negotiations result in higher salaries! Worker salary increased from {format_currency(old_salary)} to {format_currency(WORKER_SALARY)}."

        elif roll > 0.85: # Positive Event (15% chance)
            event_type = random.choice(['BOOM', 'POSITIVE_PR_PLAYER', 'TECH_BREAKTHROUGH'])
            if event_type == 'BOOM' and self.trend < 1.3:
                self.trend *= random.uniform(1.1, 1.3)
                self.last_event = "Economic boom! Market demand trend has increased."
            elif event_type == 'POSITIVE_PR_PLAYER':
                player = businesses[0] # Assuming player is first
                if not player.bankrupt and player.marketing_level < 10:
                     player.marketing_level = min(10, player.marketing_level + random.randint(1, 2))
                     self.last_event = f"Positive PR for {player.name}! Your product gained unexpected attention (Marketing Level up!)."
                else:
                     self.last_event = "Market conditions remain stable." # Fallback if player PR not possible
            elif event_type == 'TECH_BREAKTHROUGH':
                 points = random.randint(30, 60)
                 affected_biz_count = 0
                 for biz in businesses:
                     if not biz.bankrupt:
                         biz.rnd_points += points
                         affected_biz_count +=1
                 self.last_event = f"Industry technology breakthrough assists R&D! (+{points} R&D points for {affected_biz_count} businesses)."
        # Else (70% chance): No significant event


class Game:
    """Manages the game state and loop."""
    def __init__(self):
        self.player_business = Business(name="Player Inc.")
        # Add AI competitor(s)
        self.competitors = [AI_Business(name="CompetitorCorp", difficulty=0.6)]
        self.businesses = [self.player_business] + self.competitors # Master list
        self.market = Market()
        self.turn = 1
        self.game_over = False

    # --- Save/Load Methods ---
    def save_game(self, filename=SAVE_FILENAME):
        """Saves the current game state."""
        try:
            with open(filename, 'wb') as f:
                pickle.dump(self, f) # Save the entire Game object
            print(f"Game saved successfully to {filename}")
        except Exception as e:
            print(f"Error saving game: {e}")

    @staticmethod
    def load_game(filename=SAVE_FILENAME):
        """Loads a game state from a file."""
        try:
            with open(filename, 'rb') as f:
                game_state = pickle.load(f)
            print(f"Game loaded successfully from {filename}")
            return game_state
        except FileNotFoundError:
            print(f"Save file '{filename}' not found. Starting a new game.")
            return None
        except Exception as e:
            print(f"Error loading game: {e}. Starting a new game.")
            return None

    # --- Game Flow Methods ---
    def print_status(self):
        """Prints the current game status."""
        player = self.player_business
        print("\n" + "="*50)
        print(f"Turn: {self.turn} / {MAX_TURNS} | Goal: {format_currency(TARGET_NET_WORTH)} Net Worth")
        print(f"Market Trend: {self.market.trend:.2f} | Last Event: {self.market.last_event}")
        print("-"*50)
        print(f"--- {player.name} Status ---")
        print(f"Net Worth: {format_currency(player.calculate_net_worth())} | Cash: {format_currency(player.money)}")
        print(f"Loan: {format_currency(player.loan_amount)} | Inventory: {player.inventory} units")
        print(f"Workers: {player.workers} | Capacity: {player.max_production_capacity} units/turn | Salary/Worker: {format_currency(WORKER_SALARY)}")
        print(f"Price: {format_currency(player.price_per_unit)} | Prod Cost: {format_currency(player.production_cost)}")
        print(display_bar("Quality", player.product_quality, 10))
        print(display_bar("Marketing", player.marketing_level, 10))
        print(f"R&D Progress: {player.rnd_points} / {RND_POINTS_PER_UPGRADE} points")
        print(f"Last Turn: {player.last_turn_sales} sales, {format_currency(player.last_turn_profit)} profit")
        print(f"Total Profit: {format_currency(player.total_profit)}")

        # Competitor Summary
        for comp in self.competitors:
             if not comp.bankrupt:
                 print("-"*20)
                 print(f"--- {comp.name} Status (Estimate) ---")
                 print(f"Price: {format_currency(comp.price_per_unit)} | Quality: {comp.product_quality}/10 | Marketing: {comp.marketing_level}/10")
                 print(f"Inventory: {comp.inventory} | Workers: {comp.workers}")
             else:
                 print(f"--- {comp.name} is BANKRUPT ---")
        print("="*50 + "\n")


    def get_player_actions(self):
        """Gets the player's decisions for the turn."""
        player = self.player_business
        print(f"--- {player.name}: Decisions for Turn {self.turn} ---")

        # 1. Staffing (Hire/Fire) - Do this first as it affects capacity
        print(f"\nCurrent Workers: {player.workers}. Max Production Capacity: {player.max_production_capacity}")
        print(f"Cost per worker: Hire={format_currency(HIRING_COST_PER_WORKER)}, Fire={format_currency(FIRING_COST_PER_WORKER)}, Salary={format_currency(WORKER_SALARY)}/turn")
        max_affordable_hires = int((player.money - 500) // HIRING_COST_PER_WORKER) if HIRING_COST_PER_WORKER > 0 else 1000 # Keep small buffer
        hire_workers = get_int_input(f"How many workers to HIRE? (Max affordable: ~{max_affordable_hires}) ", 0, max_affordable_hires)
        if hire_workers > 0:
            cost = hire_workers * HIRING_COST_PER_WORKER
            player.money -= cost
            player.workers += hire_workers
            print(f"Hired {hire_workers} workers. Cost: {format_currency(cost)}. Total workers: {player.workers}.")

        max_fires = player.workers -1 # Can't fire everyone, need at least 1 maybe? Or 0? Let's allow 0.
        max_fires = player.workers
        max_affordable_fires = int((player.money - 500) // FIRING_COST_PER_WORKER) if FIRING_COST_PER_WORKER > 0 else max_fires
        # Cannot fire more than you can afford severance for, unless money is negative? (Complex rule, simplify for now)
        can_fire = min(max_fires, max_affordable_fires if player.money > 0 else max_fires)

        fire_workers = 0
        if player.workers > 0 :
             fire_workers = get_int_input(f"How many workers to FIRE? (Max: {player.workers}, Affordable Severance: {can_fire}) ", 0, player.workers)
             if fire_workers > 0:
                 if fire_workers > can_fire:
                     print(f"WARN: You cannot afford the severance cost ({format_currency(fire_workers * FIRING_COST_PER_WORKER)}) for {fire_workers} workers.")
                     print(f"Reducing firing count to affordable maximum: {can_fire}")
                     fire_workers = can_fire

                 if fire_workers > 0:
                     cost = fire_workers * FIRING_COST_PER_WORKER
                     player.money -= cost
                     player.workers -= fire_workers
                     print(f"Fired {fire_workers} workers. Severance Cost: {format_currency(cost)}. Remaining workers: {player.workers}.")

        print(f"Updated Worker Count: {player.workers}. New Max Production Capacity: {player.max_production_capacity}")

        # 2. Production
        current_capacity = player.max_production_capacity
        max_affordable_prod = int(player.money // player.production_cost) if player.production_cost > 0 else 0
        max_produce = min(current_capacity, max_affordable_prod)
        print(f"\nYou can produce up to {max_produce} units (Capacity: {current_capacity}, Affordable: {max_affordable_prod}). Cost: {format_currency(player.production_cost)} each.")
        produce_units = get_int_input(f"How many units to produce? (Current Inv: {player.inventory}) ", 0, max_produce)
        if produce_units > 0:
            cost_to_produce = produce_units * player.production_cost
            player.money -= cost_to_produce
            player.inventory += produce_units
            print(f"Produced {produce_units} units. Cost: {format_currency(cost_to_produce)}. Cash remaining: {format_currency(player.money)}")

        # 3. Pricing
        print(f"\nCurrent price: {format_currency(player.price_per_unit)}")
        new_price = get_int_input("Set new price per unit: $", 1) # Price must be at least $1
        player.price_per_unit = new_price

        # 4. Marketing Investment
        current_marketing_cost = int(MARKETING_COST_FACTOR * (player.marketing_level ** 1.5)) # Increasing cost
        print(f"\nCurrent Marketing Level: {player.marketing_level}/10")
        if player.marketing_level < 10:
            print(f"Cost to increase Marketing Level by 1: ~{format_currency(current_marketing_cost)}")
            max_affordable_marketing = int(player.money)
            invest_marketing = get_int_input(f"How much to invest in Marketing? (Enter 0 or amount >= cost) $", 0, max_affordable_marketing)
            if invest_marketing >= current_marketing_cost and player.marketing_level < 10:
                 player.marketing_level += 1
                 player.money -= current_marketing_cost # Charge the cost for the level increase
                 print(f"Marketing level increased to {player.marketing_level}! Cost: {format_currency(current_marketing_cost)}")
            elif invest_marketing > 0:
                 print(f"Investment of {format_currency(invest_marketing)} is not enough to increase marketing level (requires ~{format_currency(current_marketing_cost)}). No change.")
                 # No partial progress for simplicity now
        else:
            print("Marketing is already at maximum level (10).")


        # 5. R&D Investment
        current_rnd_cost = int(RND_COST_FACTOR * (player.product_quality + max(1, 25 - player.production_cost))) # Cost increases with progress (cost component adjusted)
        print(f"\nCurrent Quality: {player.product_quality}/10, Prod Cost: {format_currency(player.production_cost)}")
        print(f"R&D Progress: {player.rnd_points}/{RND_POINTS_PER_UPGRADE}")
        print(f"Approx. Cost per R&D point: ~${max(0.01, current_rnd_cost / RND_POINTS_PER_UPGRADE):.2f}") # Rough estimate, ensure not zero
        max_affordable_rnd = int(player.money)
        invest_rnd = get_int_input(f"How much to invest in R&D? (Max: {format_currency(max_affordable_rnd)}) $", 0, max_affordable_rnd)
        if invest_rnd > 0:
            # Slightly more predictable point gain
            cost_per_point = max(0.01, current_rnd_cost / RND_POINTS_PER_UPGRADE)
            points_gained = int(invest_rnd / cost_per_point) if cost_per_point > 0 else 0

            actual_cost = points_gained * cost_per_point
            player.rnd_points += points_gained
            player.money -= actual_cost # Deduct actual cost based on points gained
            print(f"Invested {format_currency(actual_cost)} in R&D, gained {points_gained} points.")

            # Check for R&D breakthroughs
            while player.rnd_points >= RND_POINTS_PER_UPGRADE:
                player.rnd_points -= RND_POINTS_PER_UPGRADE
                quality_cap = player.product_quality >= 10
                cost_floor = player.production_cost <= 5 # Min production cost

                if quality_cap and cost_floor:
                    print("R&D Breakthrough! But Quality and Production Cost are already maxed/minned.")
                    player.rnd_points = 0 # Reset points if nothing to improve
                    break

                # Player Choice for R&D outcome
                print("\nR&D Breakthrough!")
                options = []
                if not quality_cap: options.append("Improve Quality")
                if not cost_floor: options.append("Reduce Production Cost")

                if not options: # Should not happen based on outer check, but safeguard
                     print("No available upgrades.")
                     break

                print("Choose your focus:")
                for i, opt in enumerate(options):
                    print(f"  {i+1}. {opt}")

                choice = get_int_input("Enter choice number: ", 1, len(options))
                chosen_option = options[choice-1]

                if chosen_option == "Improve Quality":
                   player.product_quality += 1
                   print("Success! Product Quality increased to {}!".format(player.product_quality))
                elif chosen_option == "Reduce Production Cost":
                   reduction = random.randint(1, 3)
                   player.production_cost = max(5, player.production_cost - reduction)
                   print(f"Success! Production Cost reduced by {format_currency(reduction)} to {format_currency(player.production_cost)}!")


        # 6. Loan Management
        print(f"\nCurrent Loan: {format_currency(player.loan_amount)}")
        max_loan = player.get_max_loan()
        print(f"Maximum additional loan available: {format_currency(max_loan)}")
        take_loan = get_int_input(f"How much new loan to take? (Enter 0 for none) $", 0, int(max_loan))
        if take_loan > 0:
            player.loan_amount += take_loan
            player.money += take_loan
            print(f"Took out loan of {format_currency(take_loan)}. Total loan: {format_currency(player.loan_amount)}. Cash: {format_currency(player.money)}")

        max_repayment = min(player.loan_amount, player.money)
        if player.loan_amount > 0:
            repay_loan = get_int_input(f"How much loan to repay? (Max: {format_currency(max_repayment)}) $", 0, int(max_repayment))
            if repay_loan > 0:
                player.loan_amount -= repay_loan
                player.money -= repay_loan
                print(f"Repaid {format_currency(repay_loan)} of loan. Remaining loan: {format_currency(player.loan_amount)}. Cash: {format_currency(player.money)}")

        # 7. Save Game Option
        save_choice = input("Save game before processing turn? (y/N): ").strip().lower()
        if save_choice == 'y':
            self.save_game()


    def process_turn(self):
        """Simulates the market and updates business state for all."""
        print("\n--- Processing Turn {} ---".format(self.turn))
        time.sleep(0.5) # Pause for effect

        # 1. AI makes decisions
        print("Competitors are making their moves...")
        for ai in self.competitors:
            if not ai.bankrupt:
                ai.make_decisions(self.market.trend, self.player_business)
        time.sleep(0.5)

        # 2. Market Simulation & Events
        self.market.update_trend()
        self.market.generate_event(self.businesses) # Pass all businesses to events
        if self.market.last_event != "No significant market events.":
             print(f"Market Event: {self.market.last_event}")
             time.sleep(1)


        # 3. Calculate Demand and Sales Split
        total_demand = self.market.calculate_total_potential_demand(self.businesses)
        print(f"Market Analysis: Estimated total potential demand this turn is {total_demand} units.")

        market_sales = self.market.calculate_market_shares(self.businesses, total_demand)
        print("Calculating market share and sales...")
        time.sleep(0.5)

        # 4. Process Sales Results for each Business
        total_revenue_all = 0
        total_cogs_all = 0
        total_profit_all = 0
        total_salaries_all = 0

        for biz in self.businesses:
            if biz.bankrupt: continue

            units_sold = market_sales.get(biz.name, 0)
            revenue, cogs, profit = biz.process_sales(units_sold)
            total_revenue_all += revenue
            total_cogs_all += cogs
            total_profit_all += profit

            if not biz.is_ai: # Print detailed player results
                if units_sold > 0:
                     print(f"\n--- {biz.name} Sales Results ---")
                     print(f"Sold {units_sold} units at {format_currency(biz.price_per_unit)} each.")
                     print(f"Revenue: {format_currency(revenue)}")
                     print(f"Cost of Goods Sold: {format_currency(cogs)}")
                     print(f"Gross Profit this turn: {format_currency(profit)}")
                else:
                     print(f"\n--- {biz.name} Sales Results ---")
                     print("Sales: No units sold this turn.")

        # 5. Apply Salaries and Interest
        print("\nProcessing salaries and interest...")
        for biz in self.businesses:
             if biz.bankrupt: continue
             salaries, _, _ = biz.apply_interest_and_salaries()
             total_salaries_all += salaries
             if not biz.is_ai:
                 print(f"{biz.name} - Salaries Paid: {format_currency(salaries)}")
                 print(f"{biz.name} - Cash after expenses: {format_currency(biz.money)}")

        # 6. Check for Bankruptcy
        for biz in self.businesses:
            if not biz.bankrupt and biz.check_bankruptcy():
                 print(f"\n!!! ALERT: {biz.name} has declared BANKRUPTCY! !!!")
                 time.sleep(1)
                 # Optional: Remove bankrupt AI from active list?
                 # self.businesses = [b for b in self.businesses if not b.bankrupt]
                 # self.competitors = [c for c in self.competitors if not c.bankrupt]


        # 7. Advance Turn Counter
        self.turn += 1


    def check_game_over(self):
        """Checks for win/loss conditions."""
        player = self.player_business

        # Loss Condition 1: Player Bankruptcy
        if player.bankrupt:
            print("\n" + "#"*40)
            print("             GAME OVER - BANKRUPTCY!")
            print(f"Your company's net worth and cash dropped below zero.")
            print(f"You survived {self.turn -1} turns.")
            print(f"Total Profit achieved: {format_currency(player.total_profit)}")
            print("#"*40)
            self.game_over = True
            return True

        net_worth = player.calculate_net_worth()

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

            print(f"Total Profit achieved: {format_currency(player.total_profit)}")
            print("#"*40)
            self.game_over = True
            return True

        # Win Condition: Reached target net worth before time runs out
        if net_worth >= TARGET_NET_WORTH:
            print("\n" + "*"*40)
            print("         CONGRATULATIONS - YOU WIN!")
            print(f"You reached the target net worth of {format_currency(TARGET_NET_WORTH)}!")
            print(f"Final Net Worth: {format_currency(net_worth)}")
            print(f"Achieved in {self.turn -1} turns.")
            print(f"Total Profit: {format_currency(player.total_profit)}")
            print("*"*40)
            self.game_over = True
            return True

        return False

    def run(self):
        """Main game loop."""
        print("\nWelcome to Business Tycoon Simulator v1!")
        print(f"Goal: Reach {format_currency(TARGET_NET_WORTH)} Net Worth in {MAX_TURNS} months.")
        print("Manage production, pricing, staffing, marketing, R&D, and loans.")
        print("Compete against CompetitorCorp!")
        print("Good luck!\n")

        while not self.game_over:
            self.print_status()
            if self.check_game_over():
                break
            self.get_player_actions()
            self.process_turn()

        print("\nThank you for playing!")

# --- Run the Game ---
if __name__ == "__main__":
    game = None
    if os.path.exists(SAVE_FILENAME):
        load_choice = input(f"Save file '{SAVE_FILENAME}' found. Load game? (Y/n): ").strip().lower()
        if load_choice != 'n':
            game = Game.load_game(SAVE_FILENAME)

    if game is None: # If no save file or user chose not to load
        game = Game()

    if game: # Check if game object was successfully created or loaded
       game.run()