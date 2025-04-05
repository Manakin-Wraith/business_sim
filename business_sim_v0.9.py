import random
import time
import math
import pickle # For saving/loading
import os # For checking if save file exists

# --- Configuration ---
INITIAL_MONEY = 10000
TARGET_NET_WORTH = 25000 # Reset to a higher goal for more challenge
MAX_TURNS = 120 # Represents 10 years (months)
NUM_INITIAL_COMPETITORS = 2 # <<< NEW: Define number of starting AIs

BASE_DEMAND = 200 # Increased base demand slightly to support more players
DEMAND_PRICE_SENSITIVITY = 1.6
DEMAND_QUALITY_SENSITIVITY = 1.3
DEMAND_MARKETING_SENSITIVITY = 1.1
COMPETITION_SENSITIVITY = 0.75 # Slightly higher sensitivity with more players

INITIAL_PROD_COST = 8 # Reset to previous default
INITIAL_QUALITY = 3
INITIAL_MARKETING_LVL = 1

INITIAL_WORKERS = 0 # Reset to previous default
WORKER_SALARY = 150
MAX_PROD_PER_WORKER = 10
HIRING_COST_PER_WORKER = 250
FIRING_COST_PER_WORKER = 500

RND_COST_FACTOR = 600
RND_POINTS_PER_UPGRADE = 120
MARKETING_COST_FACTOR = 400

INTEREST_RATE = 0.05 # Reset to previous default
LOAN_INTEREST_RATE = 0.10 # Reset to previous default
MAX_LOAN_RATIO = 2.0

SAVE_FILENAME = "business_sim_save.pkl"

# --- Helper Functions (Keep as before) ---
def format_currency(amount):
    return "${:,.2f}".format(amount)

def get_int_input(prompt, min_val=None, max_val=None):
    while True:
        try:
            value_str = input(prompt).strip()
            if not value_str:
                 if min_val is not None and 0 < min_val: print(f"Input cannot be empty."); continue
                 else: value = 0
            else: value = int(value_str)
            if min_val is not None and value < min_val: print(f"Value must be at least {min_val}.")
            elif max_val is not None and value > max_val: print(f"Value must be no more than {max_val}.")
            else: return value
        except ValueError: print("Invalid input. Please enter a whole number.")

def display_bar(label, value, max_value, length=20):
    value = max(0, min(value, max_value))
    filled_length = int(length * value / max_value)
    bar = '█' * filled_length + '-' * (length - filled_length)
    return f"{label:<12} [{bar}] {value}/{max_value}"

# --- Game Classes (Business, AI_Business, Market - Keep as before) ---
class Business:
    # ... No changes needed in Business class definition ...
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
        self.workers = INITIAL_WORKERS
        self.bankrupt = False # Flag if bankrupt

        # Financial tracking for the last completed turn
        self.last_turn_sales_units = 0
        self.last_turn_revenue = 0
        self.last_turn_cogs = 0
        self.last_turn_gross_profit = 0
        self.last_turn_salaries = 0
        self.last_turn_marketing_spent = 0
        self.last_turn_rnd_spent = 0
        self.last_turn_interest_paid = 0
        self.last_turn_hiring_cost = 0
        self.last_turn_firing_cost = 0
        self.last_turn_loan_repayment = 0
        self.last_turn_net_income = 0
        self.total_gross_profit = 0
        self.total_net_income = 0

    @property
    def max_production_capacity(self): return self.workers * MAX_PROD_PER_WORKER
    def calculate_assets(self): return self.money + (self.inventory * self.production_cost)
    def calculate_net_worth(self): return self.calculate_assets() - self.loan_amount
    def get_max_loan(self): return max(0, (self.calculate_assets() * MAX_LOAN_RATIO) - self.loan_amount)

    def pay_salaries(self):
        salary_cost = self.workers * WORKER_SALARY
        self.money -= salary_cost
        self.last_turn_salaries = salary_cost
        return salary_cost

    def apply_interest(self, loan_balance_at_start_of_period):
        self.last_turn_interest_paid = 0
        interest_earned = 0
        if self.money > 0:
            interest_earned = self.money * (INTEREST_RATE / 12)
            self.money += interest_earned
        if loan_balance_at_start_of_period > 0:
            interest_paid = loan_balance_at_start_of_period * (LOAN_INTEREST_RATE / 12)
            self.money -= interest_paid
            self.last_turn_interest_paid = interest_paid
        return interest_earned, self.last_turn_interest_paid

    def process_sales(self, units_sold):
        self.last_turn_sales_units = 0; self.last_turn_revenue = 0
        self.last_turn_cogs = 0; self.last_turn_gross_profit = 0
        if units_sold > 0 and units_sold <= self.inventory:
            revenue = units_sold * self.price_per_unit
            cost_of_goods_sold = units_sold * self.production_cost
            gross_profit = revenue - cost_of_goods_sold
            self.inventory -= units_sold; self.money += revenue
            self.last_turn_sales_units = units_sold; self.last_turn_revenue = revenue
            self.last_turn_cogs = cost_of_goods_sold; self.last_turn_gross_profit = gross_profit
            self.total_gross_profit += gross_profit
            return revenue, cost_of_goods_sold, gross_profit
        return 0, 0, 0

    def check_bankruptcy(self):
        if self.calculate_net_worth() < 0 and self.money < 0: self.bankrupt = True; return True
        return False

    def reset_turn_spending_trackers(self):
        self.last_turn_marketing_spent = 0; self.last_turn_rnd_spent = 0
        self.last_turn_hiring_cost = 0; self.last_turn_firing_cost = 0
        self.last_turn_loan_repayment = 0

class AI_Business(Business):
    # ... No changes needed in AI_Business class definition yet ...
    """Represents an AI controlled business."""
    def __init__(self, name="Competitor", difficulty=0.5): # Added personality later
        super().__init__(name=name, is_ai=True, initial_money=INITIAL_MONEY * random.uniform(0.85, 1.0)) # Random start cash variation
        self.difficulty = difficulty # Controls general aggressiveness/efficiency
        # Personality traits to be added later
        # self.personality = personality # e.g., "Pricer", "Marketer", "QualityLeader", "Balanced"

        # Tuning parameters based on difficulty/personality
        base_ratio = 1.5
        base_aggressiveness = 0.1
        base_margin = 1.5

        # Example difficulty scaling (can be refined)
        self.target_inventory_ratio = base_ratio + (difficulty - 0.5) * 0.4 # Higher difficulty -> slightly more stock
        self.investment_aggressiveness = base_aggressiveness + (difficulty * 0.15) # Higher difficulty -> invests more %
        self.pricing_margin = base_margin + (random.uniform(-0.1, 0.2) * (1+difficulty)) # Higher difficulty -> slightly higher margin potential

        # Personality overrides/adjustments would go here later

        self.min_target_inventory = max(5, int(INITIAL_WORKERS * MAX_PROD_PER_WORKER * 0.2)) # Lowered min inv slightly

    def make_decisions(self, market_trend, player_business):
        # ... AI decision logic remains the same for now ...
        if self.bankrupt: return
        self.reset_turn_spending_trackers()

        required_cash_buffer = (self.workers * WORKER_SALARY) + (self.loan_amount * (LOAN_INTEREST_RATE / 12)) + 500 # Estimate next turn's fixed costs + buffer

        # --- 1. Production ---
        predicted_demand = 0
        if self.last_turn_sales_units > 0:
            predicted_demand = self.last_turn_sales_units * market_trend * random.uniform(0.8, 1.2)
        else:
            base_guess = self.max_production_capacity * (0.4 + 0.3 * self.difficulty)
            predicted_demand = base_guess * market_trend * random.uniform(0.7, 1.1)
            predicted_demand = max(0, predicted_demand)

        target_inventory_pred = int(predicted_demand * self.target_inventory_ratio)
        target_inventory = max(self.min_target_inventory, target_inventory_pred)
        needed_production = max(0, target_inventory - self.inventory)
        affordable_production = int(self.money // self.production_cost) if self.production_cost > 0 else 0
        produce_units = min(needed_production, self.max_production_capacity, affordable_production)

        if produce_units > 0 and self.inventory > 0 and (self.money - (produce_units * self.production_cost)) < required_cash_buffer :
             affordable_leaving_buffer = (self.money - required_cash_buffer) // self.production_cost if self.production_cost > 0 else 0
             produce_units = int(max(0, min(produce_units, affordable_leaving_buffer)))

        produce_units = max(0, produce_units)
        cost_to_produce = produce_units * self.production_cost
        self.money -= cost_to_produce; self.inventory += produce_units

        # --- 2. Pricing ---
        base_price = self.production_cost * self.pricing_margin
        if self.inventory > target_inventory * 1.5: base_price *= random.uniform(0.9, 0.98)
        elif self.inventory < target_inventory * 0.7 and self.inventory > 0: base_price *= random.uniform(1.02, 1.1)
        price_diff_factor = 1.0 + (player_business.price_per_unit - base_price) / max(1, base_price) * (self.difficulty * 0.15)
        self.price_per_unit = max(self.production_cost + 1, int(base_price * price_diff_factor))

        # --- 3. Staffing ---
        target_prod_capacity = needed_production * 1.2 + 5
        needed_workers = math.ceil(target_prod_capacity / max(1,MAX_PROD_PER_WORKER)) if MAX_PROD_PER_WORKER > 0 else self.workers
        target_workers = max(1, needed_workers + random.randint(-1, 1))

        hire_cost = 0; fire_cost = 0
        if target_workers > self.workers:
            workers_to_hire = target_workers - self.workers
            potential_hire_cost = workers_to_hire * HIRING_COST_PER_WORKER
            if self.money > potential_hire_cost + (target_workers * WORKER_SALARY) + 2000:
                self.money -= potential_hire_cost; self.workers += workers_to_hire
                hire_cost = potential_hire_cost
        elif target_workers < self.workers:
             workers_to_fire = self.workers - target_workers
             potential_fire_cost = workers_to_fire * FIRING_COST_PER_WORKER
             if self.money > potential_fire_cost + required_cash_buffer:
                 self.money -= potential_fire_cost; self.workers -= workers_to_fire
                 fire_cost = potential_fire_cost

        self.last_turn_hiring_cost = hire_cost; self.last_turn_firing_cost = fire_cost

        # --- 4. Marketing & R&D ---
        investment_budget = self.money * self.investment_aggressiveness
        marketing_investment_made = 0; rnd_investment_made = 0
        if self.money > required_cash_buffer + 1000 and investment_budget > 300:
            split = random.uniform(0.4, 0.7) # Default split
            # Personality bias would adjust split later
            marketing_budget = investment_budget * split
            rnd_budget = investment_budget * (1-split)

            # Marketing Investment
            current_marketing_cost = int(MARKETING_COST_FACTOR * (self.marketing_level ** 1.5))
            if self.marketing_level < 10 and marketing_budget >= current_marketing_cost and self.money - marketing_budget > required_cash_buffer:
                 self.money -= current_marketing_cost; self.marketing_level += 1
                 marketing_investment_made = current_marketing_cost

            # R&D Investment
            current_rnd_cost_per_point = RND_COST_FACTOR * (self.product_quality + max(1, 20 - self.production_cost)) / max(1, RND_POINTS_PER_UPGRADE) + 1
            if rnd_budget > 0 and self.money - marketing_investment_made - rnd_budget > required_cash_buffer:
                cost_per_point = max(0.01, current_rnd_cost_per_point)
                points_gained = int(rnd_budget / cost_per_point) if cost_per_point > 0 else 0
                actual_rnd_cost = points_gained * cost_per_point
                if actual_rnd_cost <= self.money - marketing_investment_made - required_cash_buffer:
                    self.money -= actual_rnd_cost; self.rnd_points += points_gained
                    rnd_investment_made = actual_rnd_cost
                    # R&D Breakthrough
                    while self.rnd_points >= RND_POINTS_PER_UPGRADE:
                        self.rnd_points -= RND_POINTS_PER_UPGRADE
                        if self.product_quality >= 10 and self.production_cost <= 5: break
                        # Personality bias for choice later
                        improve_quality_chance = 0.6 if self.product_quality < 7 else 0.3
                        if random.random() < improve_quality_chance and self.product_quality < 10: self.product_quality += 1
                        elif self.production_cost > 5: self.production_cost = max(5, self.production_cost - random.randint(1, 2))
                        elif self.product_quality < 10: self.product_quality += 1

        self.last_turn_marketing_spent = marketing_investment_made
        self.last_turn_rnd_spent = rnd_investment_made

        # --- 5. Loans ---
        projected_cash = self.money
        repaid_this_turn = 0
        if projected_cash < required_cash_buffer and self.get_max_loan() > 500:
             loan_needed = max(500, required_cash_buffer - projected_cash)
             loan_to_take = min(loan_needed, self.get_max_loan())
             self.loan_amount += loan_to_take; self.money += loan_to_take
        elif self.loan_amount > 0 and self.money > self.loan_amount * 1.5 + required_cash_buffer + 10000:
             repay_amount = min(self.loan_amount, self.money - required_cash_buffer - 5000)
             repay_amount = max(0, repay_amount)
             if repay_amount > 0:
                 self.loan_amount -= repay_amount; self.money -= repay_amount
                 repaid_this_turn = repay_amount
        self.last_turn_loan_repayment = repaid_this_turn


class Market:
    # ... No changes needed in Market class definition ...
    """Represents the market dynamics."""
    def __init__(self):
        self.current_base_demand = BASE_DEMAND
        self.trend = 1.0
        self.last_event = "No significant market events."

    def update_trend(self):
        change = random.uniform(-0.05, 0.05)
        self.trend = max(0.5, min(1.5, self.trend + change))

    def calculate_total_potential_demand(self, businesses):
        # Simple approach: average the stats of active players? Or use player as benchmark?
        # Let's average active non-bankrupt players for now
        active_biz = [b for b in businesses if not b.bankrupt]
        if not active_biz: return 0

        avg_price = sum(b.price_per_unit for b in active_biz) / len(active_biz)
        avg_quality = sum(b.product_quality for b in active_biz) / len(active_biz)
        avg_marketing = sum(b.marketing_level for b in active_biz) / len(active_biz)

        safe_price = max(1, avg_price)
        price_factor = (INITIAL_PROD_COST * 2 / safe_price) ** DEMAND_PRICE_SENSITIVITY
        quality_factor = (avg_quality / 5.0) ** DEMAND_QUALITY_SENSITIVITY
        marketing_factor = (avg_marketing / 5.0) ** DEMAND_MARKETING_SENSITIVITY

        demand = self.current_base_demand * self.trend * price_factor * quality_factor * marketing_factor
        demand *= random.uniform(0.9, 1.1) # Overall market noise
        return max(0, int(demand))

    def calculate_market_shares(self, businesses, total_demand):
        # This method inherently handles multiple businesses already
        scores = {}
        total_score = 0
        active_businesses = [b for b in businesses if not b.bankrupt and b.inventory > 0]

        if not active_businesses: return {biz.name: 0 for biz in businesses}

        for biz in active_businesses:
            price_score = (1 / max(1, biz.price_per_unit)) ** (DEMAND_PRICE_SENSITIVITY * COMPETITION_SENSITIVITY)
            quality_score = biz.product_quality ** (DEMAND_QUALITY_SENSITIVITY * COMPETITION_SENSITIVITY)
            marketing_score = biz.marketing_level ** (DEMAND_MARKETING_SENSITIVITY * COMPETITION_SENSITIVITY)
            # Add tiny score bonus for having inventory at all
            score = (price_score * quality_score * marketing_score + 0.01) * random.uniform(0.95, 1.05)
            scores[biz.name] = score
            total_score += score

        sales = {biz.name: 0 for biz in businesses}
        if total_score <= 0: return sales # Avoid division by zero

        remaining_demand = total_demand
        # Sort by score to give higher scores better chance at demand
        sorted_businesses = sorted(active_businesses, key=lambda b: scores.get(b.name, 0), reverse=True)

        # Allocate demand proportionally first pass
        temp_sales = {}
        total_allocated = 0
        for biz in sorted_businesses:
            share_ratio = scores.get(biz.name, 0) / total_score
            potential_sales = math.floor(total_demand * share_ratio) # Floor first pass
            actual_sales = min(biz.inventory, potential_sales, remaining_demand - total_allocated)
            temp_sales[biz.name] = actual_sales
            total_allocated += actual_sales

        remaining_demand_after_proportional = total_demand - total_allocated

        # Distribute remaining units one by one based on score rank (handles rounding issues)
        # and inventory limits
        if remaining_demand_after_proportional > 0:
             for biz in sorted_businesses:
                 if remaining_demand_after_proportional <= 0: break
                 # Check if they can still sell one more unit
                 if biz.inventory > temp_sales.get(biz.name, 0):
                      temp_sales[biz.name] = temp_sales.get(biz.name, 0) + 1
                      remaining_demand_after_proportional -= 1

        # Final assignment
        for name, count in temp_sales.items():
            sales[name] = count

        return sales

    def generate_event(self, businesses):
        # ... Event generation logic remains the same ...
        self.last_event = "No significant market events."
        roll = random.random()
        if roll < 0.15: # Negative Event
            event_type = random.choice(['RECESSION', 'SUPPLY_ISSUE', 'WAGE_HIKE'])
            if event_type == 'RECESSION' and self.trend > 0.7:
                self.trend *= random.uniform(0.7, 0.9); self.last_event = "Economic downturn!"
            elif event_type == 'SUPPLY_ISSUE':
                cost_increase = random.uniform(1.05, 1.20)
                for biz in businesses:
                     if not biz.bankrupt: biz.production_cost *= cost_increase
                self.last_event = f"Supply chain disruption! Prod costs up {((cost_increase-1)*100):.1f}%."
            elif event_type == 'WAGE_HIKE':
                 global WORKER_SALARY
                 old_salary = WORKER_SALARY
                 WORKER_SALARY = int(WORKER_SALARY * random.uniform(1.1, 1.25))
                 self.last_event = f"Wage hike! Salary now {format_currency(WORKER_SALARY)}."
        elif roll > 0.85: # Positive Event
            event_type = random.choice(['BOOM', 'POSITIVE_PR_PLAYER', 'TECH_BREAKTHROUGH'])
            if event_type == 'BOOM' and self.trend < 1.3:
                self.trend *= random.uniform(1.1, 1.3); self.last_event = "Economic boom!"
            elif event_type == 'POSITIVE_PR_PLAYER':
                player = businesses[0]
                if not player.bankrupt and player.marketing_level < 10:
                     player.marketing_level = min(10, player.marketing_level + random.randint(1, 2))
                     self.last_event = f"Positive PR for {player.name}! (Marketing Lvl Up)."
                else: self.last_event = "Market conditions stable."
            elif event_type == 'TECH_BREAKTHROUGH':
                 points = random.randint(30, 60)
                 for biz in businesses:
                     if not biz.bankrupt: biz.rnd_points += points
                 self.last_event = f"Tech breakthrough! (+{points} R&D points)."


class Game:
    """Manages the game state and loop."""
    def __init__(self):
        self.player_business = Business(name="Player Inc.")
        self.ai_spawn_counter = 0 # Start at 0, will increment before first use
        self.competitors = []     # Initialize as empty list
        self.businesses = [self.player_business] # Start with only player

        # <<< CHANGE: Create initial competitors in a loop >>>
        print(f"Initializing {NUM_INITIAL_COMPETITORS} competitors...")
        difficulties = [0.5, 0.7] # Example starting difficulties for 2 AIs
        for i in range(NUM_INITIAL_COMPETITORS):
            self.ai_spawn_counter += 1
            ai_name = f"Competitor Mk{self.ai_spawn_counter}"
            # Assign varying difficulties - make more robust later if needed
            ai_difficulty = difficulties[i % len(difficulties)] + random.uniform(-0.05, 0.05)
            ai_difficulty = max(0.1, min(1.0, ai_difficulty)) # Clamp difficulty 0.1-1.0

            print(f"  Creating {ai_name} with difficulty {ai_difficulty:.2f}")
            new_ai = AI_Business(name=ai_name, difficulty=ai_difficulty)
            self.competitors.append(new_ai)
            self.businesses.append(new_ai)
        # <<< END CHANGE >>>

        self.market = Market()
        self.turn = 1
        self.game_over = False

    # --- Save/Load Methods ---
    def save_game(self, filename=SAVE_FILENAME):
        try:
            with open(filename, 'wb') as f: pickle.dump(self, f)
            print(f"Game saved successfully to {filename}")
        except Exception as e: print(f"Error saving game: {e}")

    @staticmethod
    def load_game(filename=SAVE_FILENAME):
        try:
            with open(filename, 'rb') as f: game_state = pickle.load(f)
            print(f"Game loaded successfully from {filename}")
            # Compatibility checks (ensure necessary attributes exist)
            if not hasattr(game_state, 'ai_spawn_counter'): game_state.ai_spawn_counter = len(getattr(game_state, 'competitors', []))
            for biz in getattr(game_state, 'businesses', []):
                if not hasattr(biz, 'last_turn_loan_repayment'): biz.last_turn_loan_repayment = 0
                # Add other checks if more attributes are added later
            return game_state
        except FileNotFoundError: return None
        except Exception as e: print(f"Error loading game: {e}. Starting a new game."); return None

    # --- Game Flow Methods ---
    def print_status(self):
        """Prints the current game status."""
        player = self.player_business
        print("\n" + "="*60) # Wider separator
        print(f"Turn: {self.turn} / {MAX_TURNS} | Goal: {format_currency(TARGET_NET_WORTH)} Net Worth")
        print(f"Market Trend: {self.market.trend:.2f} | Last Event: {self.market.last_event}")
        print("-"*60)

        # --- Player Status ---
        print(f"--- {player.name} (You) ---")
        print(f"Net Worth: {format_currency(player.calculate_net_worth()):<25} Cash: {format_currency(player.money)}")
        print(f"Loan: {format_currency(player.loan_amount):<25} Inventory: {player.inventory} units")
        print(f"Workers: {player.workers:<3} Capacity: {player.max_production_capacity:<15} Salary/W: {format_currency(WORKER_SALARY)}")
        print(f"Price: {format_currency(player.price_per_unit):<25} Prod Cost: {format_currency(player.production_cost)}")
        print(display_bar("Quality", player.product_quality, 10))
        print(display_bar("Marketing", player.marketing_level, 10))
        print(f"R&D Pts: {player.rnd_points} / {RND_POINTS_PER_UPGRADE}")
        print(f"Total Profit: G={format_currency(player.total_gross_profit)} N={format_currency(player.total_net_income)}")

        # <<< CHANGE: Loop through all competitors for summary >>>
        print("-"*60)
        print("--- Competitor Status (Estimates) ---")
        if not self.competitors:
            print("No active competitors.")
        else:
            header = f"{'Name':<16} {'Price':<10} {'Inv':<5} {'Qual':<5} {'Mark':<5} {'Work':<5}"
            print(header)
            print("-" * len(header))
            for comp in self.competitors:
                if comp.bankrupt:
                    print(f"{comp.name:<16} {'BANKRUPT':<44}")
                else:
                    # Show key stats concisely
                    stats = (
                        f"{comp.name:<16} "
                        f"{format_currency(comp.price_per_unit):<10} "
                        f"{comp.inventory:<5} "
                        f"{comp.product_quality:<5} "
                        f"{comp.marketing_level:<5} "
                        f"{comp.workers:<5}"
                    )
                    print(stats)
        print("="*60 + "\n")
        # <<< END CHANGE >>>


    def get_player_actions(self):
        # ... Player action logic remains the same ...
        player = self.player_business
        print(f"--- {player.name}: Decisions for Turn {self.turn} ---")
        player.reset_turn_spending_trackers()
        # ... (Staffing, Production, Pricing, Marketing, R&D, Loans, Save) ...
        # 1. Staffing
        print(f"\nCurrent Workers: {player.workers}. Max Prod Capacity: {player.max_production_capacity}")
        calculated_hires = 0
        if HIRING_COST_PER_WORKER > 0:
            cash_available = player.money - 500
            if cash_available > 0: calculated_hires = int(cash_available // HIRING_COST_PER_WORKER)
        else: calculated_hires = 1000
        max_affordable_hires = max(0, calculated_hires)
        hire_workers = get_int_input(f"Hire Workers? (Max affordable: {max_affordable_hires}) ", 0, max_affordable_hires)
        if hire_workers > 0:
            cost = hire_workers * HIRING_COST_PER_WORKER
            player.money -= cost; player.workers += hire_workers; player.last_turn_hiring_cost = cost
            print(f"Hired {hire_workers}. Cost: {format_currency(cost)}. Total workers: {player.workers}.")

        if player.workers > 0 :
             max_fires = player.workers
             affordable_severance = player.money - 500
             max_affordable_fires = max_fires
             if FIRING_COST_PER_WORKER > 0 and affordable_severance < (max_fires * FIRING_COST_PER_WORKER):
                 if affordable_severance > 0: max_affordable_fires = int(affordable_severance // FIRING_COST_PER_WORKER)
                 else: max_affordable_fires = 0
             can_fire = min(max_fires, max_affordable_fires)
             fire_workers_input = get_int_input(f"Fire Workers? (Max: {player.workers}, Can afford severance for: {can_fire}) ", 0, player.workers)
             fire_workers = 0
             if fire_workers_input > can_fire: print(f"WARN: Cannot afford severance for {fire_workers_input}.")
             elif fire_workers_input > 0: fire_workers = fire_workers_input
             if fire_workers > 0:
                 cost = fire_workers * FIRING_COST_PER_WORKER
                 player.money -= cost; player.workers -= fire_workers; player.last_turn_firing_cost = cost
                 print(f"Fired {fire_workers}. Severance Cost: {format_currency(cost)}. Remaining workers: {player.workers}.")
        print(f"Updated Workers: {player.workers}. New Max Capacity: {player.max_production_capacity}")

        # 2. Production
        current_capacity = player.max_production_capacity
        max_affordable_prod = int(player.money // player.production_cost) if player.production_cost > 0 else 0
        max_produce = min(current_capacity, max_affordable_prod)
        print(f"\nProduce Units? (Max: {max_produce}, Cost/Unit: {format_currency(player.production_cost)})")
        produce_units = get_int_input(f"How many to produce? (Current Inv: {player.inventory}) ", 0, max_produce)
        if produce_units > 0:
            cost_to_produce = produce_units * player.production_cost
            player.money -= cost_to_produce; player.inventory += produce_units
            print(f"Produced {produce_units}. Cost: {format_currency(cost_to_produce)}. Cash: {format_currency(player.money)}")

        # 3. Pricing
        print(f"\nCurrent Price/Unit: {format_currency(player.price_per_unit)}")
        player.price_per_unit = get_int_input("Set new price: $", 1)

        # 4. Marketing
        current_marketing_cost = int(MARKETING_COST_FACTOR * (player.marketing_level ** 1.5))
        print(f"\nCurrent Marketing Level: {player.marketing_level}/10")
        marketing_investment_made = 0
        if player.marketing_level < 10:
            print(f"Cost to increase Level: ~{format_currency(current_marketing_cost)}")
            invest_marketing = get_int_input(f"Invest in Marketing? (0 or >= cost) $", 0, int(player.money))
            if invest_marketing >= current_marketing_cost:
                 player.marketing_level += 1; player.money -= current_marketing_cost
                 marketing_investment_made = current_marketing_cost
                 print(f"Marketing level up to {player.marketing_level}! Cost: {format_currency(current_marketing_cost)}")
            elif invest_marketing > 0: print("Investment too low.")
        else: print("Marketing maxed.")
        player.last_turn_marketing_spent = marketing_investment_made

        # 5. R&D
        current_rnd_cost = int(RND_COST_FACTOR * (player.product_quality + max(1, 25 - player.production_cost)))
        print(f"\nCurrent R&D: Qual={player.product_quality}/10, Prod Cost={format_currency(player.production_cost)}")
        print(f"R&D Progress: {player.rnd_points}/{RND_POINTS_PER_UPGRADE}")
        rnd_investment_made = 0
        invest_rnd = get_int_input(f"Invest in R&D? (Max: {format_currency(player.money)}) $", 0, int(player.money))
        if invest_rnd > 0:
            cost_per_point = max(0.01, current_rnd_cost / RND_POINTS_PER_UPGRADE)
            points_gained = int(invest_rnd / cost_per_point) if cost_per_point > 0 else 0
            actual_cost = points_gained * cost_per_point
            if actual_cost <= player.money:
                player.rnd_points += points_gained; player.money -= actual_cost
                rnd_investment_made = actual_cost
                print(f"Invested {format_currency(actual_cost)}, gained {points_gained} R&D points.")
                while player.rnd_points >= RND_POINTS_PER_UPGRADE:
                    player.rnd_points -= RND_POINTS_PER_UPGRADE
                    quality_cap = player.product_quality >= 10; cost_floor = player.production_cost <= 5
                    if quality_cap and cost_floor: print("R&D Maxed!"); player.rnd_points = 0; break
                    print("\nR&D Breakthrough!"); options = []
                    if not quality_cap: options.append("Improve Quality")
                    if not cost_floor: options.append("Reduce Production Cost")
                    if not options: break
                    print("Choose focus:"); [print(f"  {i+1}. {opt}") for i, opt in enumerate(options)]
                    choice = get_int_input("Enter choice: ", 1, len(options))
                    chosen_option = options[choice-1]
                    if chosen_option == "Improve Quality":
                       player.product_quality += 1; print(f"Quality increased to {player.product_quality}!")
                    elif chosen_option == "Reduce Production Cost":
                       reduction = random.randint(1, 3); player.production_cost = max(5, player.production_cost - reduction)
                       print(f"Prod Cost reduced by {format_currency(reduction)} to {format_currency(player.production_cost)}!")
            else: print(f"Cannot afford R&D cost {format_currency(actual_cost)}.")
        player.last_turn_rnd_spent = rnd_investment_made

        # 6. Loan Management
        print(f"\nCurrent Loan: {format_currency(player.loan_amount)}")
        max_loan = player.get_max_loan()
        print(f"Max additional loan: {format_currency(max_loan)}")
        take_loan = get_int_input(f"Take new loan? $", 0, int(max_loan))
        if take_loan > 0:
            player.loan_amount += take_loan; player.money += take_loan
            print(f"Took loan {format_currency(take_loan)}. Total: {format_currency(player.loan_amount)}. Cash: {format_currency(player.money)}")
        max_repayment = min(player.loan_amount, player.money)
        if player.loan_amount > 0:
            repay_loan = get_int_input(f"Repay loan? (Max: {format_currency(max_repayment)}) $", 0, int(max_repayment))
            if repay_loan > 0:
                player.loan_amount -= repay_loan; player.money -= repay_loan
                player.last_turn_loan_repayment = repay_loan
                print(f"Repaid {format_currency(repay_loan)}. Remaining: {format_currency(player.loan_amount)}. Cash: {format_currency(player.money)}")

        # 7. Save Game Option
        save_choice = input("Save game before processing turn? (y/N): ").strip().lower()
        if save_choice == 'y': self.save_game()

    def process_turn(self):
        # ... Processing logic remains largely the same ...
        # Loops iterating over self.businesses or self.competitors
        # will automatically handle the multiple AIs.
        # The respawn logic also handles multiple bankruptcies correctly.

        print("\n--- Processing Turn {} ---".format(self.turn))
        time.sleep(0.2) # Shorter pause

        start_of_turn_loan_balances = {biz.name: biz.loan_amount for biz in self.businesses if not biz.bankrupt}

        # 1. AI makes decisions
        print("Competitors making moves...")
        for ai in self.competitors: # Iterate over the list
            if not ai.bankrupt: ai.make_decisions(self.market.trend, self.player_business)
        time.sleep(0.2)

        # 2. Market Simulation & Events
        self.market.update_trend()
        self.market.generate_event(self.businesses) # Pass all businesses
        if self.market.last_event != "No significant market events.":
             print(f"Market Event: {self.market.last_event}"); time.sleep(0.5)

        # 3. Calculate Demand and Sales Split
        total_demand = self.market.calculate_total_potential_demand(self.businesses)
        print(f"Market Analysis: Est. total demand = {total_demand} units.")
        market_sales = self.market.calculate_market_shares(self.businesses, total_demand)
        print("Calculating market shares...")
        time.sleep(0.2)

        # 4. Process Sales Results for each Business
        print("\n--- Sales Results ---") # Header moved to Financial Summary section
        for biz in self.businesses[:]:
            if biz.bankrupt: continue
            units_sold = market_sales.get(biz.name, 0)
            biz.process_sales(units_sold)
            # Sales details are shown in the summary now

        # 5. Apply Salaries and Interest
        print("\nProcessing salaries and interest...") # Combined below
        for biz in self.businesses[:]:
             if biz.bankrupt: continue
             biz.pay_salaries()
             start_balance = start_of_turn_loan_balances.get(biz.name, 0)
             biz.apply_interest(start_balance)

        # 6. Calculate Net Income and Display Turn Summaries
        print("\n" + "="*60)
        print(f"--- Turn {self.turn} Financial Summaries ---")
        print("="*60)
        for biz in self.businesses[:]:
            if biz.bankrupt: continue # Skip bankrupt ones in summary

            total_expenses = (biz.last_turn_cogs + biz.last_turn_salaries +
                              biz.last_turn_marketing_spent + biz.last_turn_rnd_spent +
                              biz.last_turn_interest_paid + biz.last_turn_hiring_cost +
                              biz.last_turn_firing_cost)
            net_income_this_turn = biz.last_turn_revenue - total_expenses
            biz.last_turn_net_income = net_income_this_turn
            biz.total_net_income += net_income_this_turn

            print(f"\n--- {biz.name} ---")
            # Sales details incorporated here
            if biz.last_turn_sales_units > 0:
                 print(f"  Sales: {biz.last_turn_sales_units} units @ {format_currency(biz.price_per_unit)}")
                 print(f"  Revenue: {format_currency(biz.last_turn_revenue):<25} COGS: {format_currency(biz.last_turn_cogs)}")
                 print(f"  Gross Profit: {format_currency(biz.last_turn_gross_profit)}")
            else:
                 had_inventory = biz.inventory + biz.last_turn_sales_units > 0
                 reason = "(Demand/Price)" if had_inventory else "(No inventory)"
                 print(f"  Sales: No units sold {reason}")

            print(f"  Expenses:")
            exp_details = f"    Sal: {format_currency(biz.last_turn_salaries)}"
            if biz.last_turn_marketing_spent > 0: exp_details += f" | Mkt: {format_currency(biz.last_turn_marketing_spent)}"
            if biz.last_turn_rnd_spent > 0: exp_details += f" | R&D: {format_currency(biz.last_turn_rnd_spent)}"
            if biz.last_turn_interest_paid > 0: exp_details += f" | Int: {format_currency(biz.last_turn_interest_paid)}"
            if biz.last_turn_hiring_cost > 0: exp_details += f" | Hire: {format_currency(biz.last_turn_hiring_cost)}"
            if biz.last_turn_firing_cost > 0: exp_details += f" | Fire: {format_currency(biz.last_turn_firing_cost)}"
            print(exp_details)
            print(f"    Total Expenses:     {format_currency(total_expenses)}") # Implied
            if biz.last_turn_loan_repayment > 0:
                 print(f"  Loan Repaid: {format_currency(biz.last_turn_loan_repayment)}")
            print(f"  Net Income: {format_currency(biz.last_turn_net_income):<25} Cash Now: {format_currency(biz.money)}")
            print("-" * 40)
            time.sleep(0.1) # Optional brief pause per summary

        # 7. Check for Bankruptcy AND Handle Respawn
        bankrupt_ais_to_remove = []
        new_ais_to_add = []
        for biz in self.businesses:
            if biz.bankrupt: continue
            if biz.check_bankruptcy():
                 print(f"\n!!! ALERT: {biz.name} has declared BANKRUPTCY! !!!")
                 time.sleep(0.5)
                 if biz.is_ai:
                     print(f"--- {biz.name} exits the market. ---")
                     bankrupt_ais_to_remove.append(biz)
                     self.ai_spawn_counter += 1
                     new_ai_name = f"Competitor Mk{self.ai_spawn_counter}"
                     print(f"+++ {new_ai_name} enters the market! +++")
                     new_competitor = AI_Business(name=new_ai_name, difficulty=random.uniform(0.4, 0.7))
                     new_ais_to_add.append(new_competitor)
                     time.sleep(0.5)

        if bankrupt_ais_to_remove or new_ais_to_add:
             print("\nUpdating competitor list...")
             for ai in bankrupt_ais_to_remove:
                 if ai in self.businesses: self.businesses.remove(ai)
                 if ai in self.competitors: self.competitors.remove(ai)
                 print(f"Removed {ai.name}.")
             for ai in new_ais_to_add:
                 if ai not in self.businesses: self.businesses.append(ai)
                 if ai not in self.competitors: self.competitors.append(ai)
                 print(f"Added {ai.name}.")
             time.sleep(0.5)


        # 8. Advance Turn Counter
        self.turn += 1


    def check_game_over(self):
        # ... Game Over logic remains the same ...
        player = self.player_business
        if player.bankrupt:
            print("\n" + "#"*40); print("             GAME OVER - BANKRUPTCY!")
            print(f"Survived {self.turn -1} turns. Total Net Income: {format_currency(player.total_net_income)}")
            print("#"*40); self.game_over = True; return True
        net_worth = player.calculate_net_worth()
        if self.turn > MAX_TURNS:
            print("\n" + "#"*40); print("              GAME OVER - OUT OF TIME!")
            print(f"Completed {MAX_TURNS} turns. Final Net Worth: {format_currency(net_worth)}")
            if net_worth >= TARGET_NET_WORTH: print("             -- YOU WIN! (Time Limit Victory) --")
            else: print(f"Target ({format_currency(TARGET_NET_WORTH)}) not reached.\n             -- YOU LOST --")
            print(f"Total Net Income achieved: {format_currency(player.total_net_income)}")
            print("#"*40); self.game_over = True; return True
        if net_worth >= TARGET_NET_WORTH:
            print("\n" + "*"*40); print("         CONGRATULATIONS - YOU WIN!")
            print(f"Reached target net worth of {format_currency(TARGET_NET_WORTH)}!")
            print(f"Final Net Worth: {format_currency(net_worth)} in {self.turn -1} turns.")
            print(f"Total Net Income: {format_currency(player.total_net_income)}")
            print("*"*40); self.game_over = True; return True
        return False


    def run(self):
        # ... Run logic remains the same ...
        print("\nWelcome to Business Tycoon Simulator v0.9!") # Version bump
        print(f"Goal: Reach {format_currency(TARGET_NET_WORTH)} Net Worth in {MAX_TURNS} months.")
        print(f"Compete against {len(self.competitors)} initial competitor(s)!")
        print("Good luck!\n")
        while not self.game_over:
            self.print_status()
            if self.check_game_over(): break
            self.get_player_actions()
            self.process_turn()
        print("\nThank you for playing!")


# --- Run the Game (Keep as before) ---
if __name__ == "__main__":
    game = None
    if os.path.exists(SAVE_FILENAME):
        load_choice = input(f"Save file '{SAVE_FILENAME}' found. Load game? (Y/n): ").strip().lower()
        if load_choice != 'n':
            game = Game.load_game(SAVE_FILENAME)
            if game is None: print("Loading failed, starting new game.")
        else: print("Starting a new game...")
    else: print("No save file found. Starting a new game...")

    if game is None: game = Game()

    if game: game.run()