**--- Game Setup ---**

*   `INITIAL_MONEY = 10000`
    *   **What it is:** The starting cash amount for both the player and the AI competitor(s).
    *   **Tweak Impact:**
        *   **Increase:** Makes the start easier. Allows for more initial production, hiring, or investment without needing immediate loans. Reduces early-game pressure.
        *   **Decrease:** Makes the start harder. Forces very careful spending, immediate loan consideration, or slower initial growth. Increases early-game pressure.

*   `TARGET_NET_WORTH = 25000`
    *   **What it is:** The primary win condition. The player needs to reach this net worth (Assets - Liabilities). *Note: Your current value (25k) is quite low compared to the starting money (10k), making the game potentially very short/easy. You might want `100000` or `150000` for a longer game.*
    *   **Tweak Impact:**
        *   **Increase:** Makes the game longer and more challenging. Requires sustained growth and profitability.
        *   **Decrease:** Makes the game shorter and easier to win quickly.

*   `MAX_TURNS = 36`
    *   **What it is:** The maximum number of turns (months) the game lasts. If the target net worth isn't reached by this turn, the game ends (win or lose based on whether the target was met).
    *   **Tweak Impact:**
        *   **Increase:** Gives the player more time to reach the goal, potentially making it easier if they have slow but steady growth. Also allows for longer-term strategies.
        *   **Decrease:** Creates more time pressure. Forces faster growth and quicker decision-making. Makes the game harder if the target net worth is high.

**--- Market Dynamics ---**

*   `BASE_DEMAND = 150`
    *   **What it is:** The theoretical maximum market demand *before* factoring in price, quality, marketing, trends, or competition. Represents the overall size of the market potential in a "neutral" state.
    *   **Tweak Impact:**
        *   **Increase:** Creates a larger overall market. More potential sales for everyone, potentially making growth easier if supply can keep up. Might make competition effects less harsh initially.
        *   **Decrease:** Shrinks the overall market. Fewer potential sales, making growth harder and competition more intense for the limited demand.

*   `DEMAND_PRICE_SENSITIVITY = 1.6`
    *   **What it is:** An exponent determining how sharply demand reacts to price changes. It affects how much demand drops as your price increases above a baseline, and how much it increases as your price drops.
    *   **Tweak Impact:**
        *   **Increase:** Makes customers *more* sensitive to price. Small price increases will cause a *larger* drop in demand. Pricing strategy becomes critical. Undercutting competitors is more effective.
        *   **Decrease:** Makes customers *less* sensitive to price. You can charge higher prices without losing as many customers. Quality and marketing might become relatively more important than price.

*   `DEMAND_QUALITY_SENSITIVITY = 1.3`
    *   **What it is:** An exponent determining how much demand reacts to product quality (relative to a baseline quality of 5).
    *   **Tweak Impact:**
        *   **Increase:** Makes customers value quality *more*. High quality products gain a significantly larger demand boost. Investing in R&D for quality becomes more rewarding. Low quality is punished more harshly.
        *   **Decrease:** Makes quality less important for demand. Price and marketing might become relatively more impactful. R&D for quality has less payoff in terms of sales volume.

*   `DEMAND_MARKETING_SENSITIVITY = 1.1`
    *   **What it is:** An exponent determining how much demand reacts to your marketing level (relative to a baseline level of 5).
    *   **Tweak Impact:**
        *   **Increase:** Makes marketing efforts *more* effective. Higher marketing levels provide a bigger boost to demand. Investing in marketing becomes more important.
        *   **Decrease:** Makes marketing less impactful on demand volume. Price and quality might become relatively more important. Spending on marketing yields lower returns in sales.

*   `COMPETITION_SENSITIVITY = 0.7`
    *   **What it is:** Controls how strongly the *relative* difference in price, quality, and marketing between you and your competitors affects the *market share split*. A higher value means small advantages/disadvantages have a bigger impact on who gets the sales. (Note: The price/quality/marketing sensitivities above affect the *total* demand calculation, while this affects the *split*).
    *   **Tweak Impact:**
        *   **Increase (towards 1.0+):** Makes the market highly competitive. Being slightly better than competitors in price/quality/marketing grants a much larger share of the available sales. Being slightly worse is heavily punished. Cut-throat environment.
        *   **Decrease (towards 0.0):** Makes the market less directly competitive. Market share is less affected by small differences between companies. Sales might be split more evenly, even if one company is slightly better. Factors other than direct comparison (like overall market trend, absolute stats) become relatively more important for individual sales.

**--- Initial Product/Business State ---**

*   `INITIAL_PROD_COST = 8`
    *   **What it is:** The starting cost to produce one unit of your product.
    *   **Tweak Impact:**
        *   **Increase:** Higher starting costs mean lower initial profit margins. Requires higher pricing or faster R&D for cost reduction. Makes the start harder financially.
        *   **Decrease:** Lower starting costs mean higher initial profit margins. Easier to make money early on. Less pressure on R&D for cost reduction initially. Makes the start easier.

*   `INITIAL_QUALITY = 3` (Scale of 1-10)
    *   **What it is:** The starting quality level of your product.
    *   **Tweak Impact:**
        *   **Increase:** Starts with a better product, leading to higher initial demand (depending on sensitivity). Less immediate pressure on R&D for quality improvement. Easier start.
        *   **Decrease:** Starts with a lower quality product, potentially hurting initial demand. Increases pressure to invest in R&D for quality early. Harder start.

*   `INITIAL_MARKETING_LVL = 1` (Scale of 1-10)
    *   **What it is:** The starting marketing level.
    *   **Tweak Impact:**
        *   **Increase:** Higher initial marketing leads to higher initial demand (depending on sensitivity). Less pressure to invest in marketing immediately. Easier start.
        *   **Decrease:** Lower initial marketing results in lower initial demand. Increases pressure to invest in marketing early. Harder start.

**--- Staffing/Production ---**

*   `INITIAL_WORKERS = 0`
    *   **What it is:** The number of workers the player and AI start with.
    *   **Tweak Impact:**
        *   **Increase:** Starts with some production capacity, allowing immediate production without hiring costs. Easier start.
        *   **Decrease (to 0):** Forces the player/AI to spend money on hiring costs *immediately* if they want to produce anything in the first turn. Makes the start harder and adds an essential first decision. *(Your current value of 0 forces hiring)*.

*   `WORKER_SALARY = 150`
    *   **What it is:** The cost per worker, per turn (month). A major recurring expense.
    *   **Tweak Impact:**
        *   **Increase:** Makes labor more expensive. Reduces profit margins, makes having a large workforce costly. Increases financial pressure.
        *   **Decrease:** Makes labor cheaper. Improves profit margins, makes scaling up production less costly. Reduces financial pressure.

*   `MAX_PROD_PER_WORKER = 10`
    *   **What it is:** How many units one worker can produce in a single turn. Determines production capacity (`Workers * MAX_PROD_PER_WORKER`).
    *   **Tweak Impact:**
        *   **Increase:** Each worker is more productive. Need fewer workers (and thus lower salary costs) to achieve a certain production level. Makes scaling production cheaper.
        *   **Decrease:** Each worker is less productive. Need more workers (higher salary costs) to produce the same amount. Makes scaling production more expensive.

*   `HIRING_COST_PER_WORKER = 250`
    *   **What it is:** The one-time cost paid when hiring a new worker.
    *   **Tweak Impact:**
        *   **Increase:** Makes expanding the workforce more expensive. Discourages rapid hiring/scaling.
        *   **Decrease:** Makes expansion cheaper and easier. Allows for faster scaling of production capacity.

*   `FIRING_COST_PER_WORKER = 500`
    *   **What it is:** The one-time cost (severance) paid when firing a worker.
    *   **Tweak Impact:**
        *   **Increase:** Makes downsizing the workforce more expensive. Discourages reactive firing; encourages keeping workers even during downturns if cash allows. Adds risk to over-hiring.
        *   **Decrease:** Makes downsizing cheaper. Allows for more flexibility in adjusting workforce size to match demand fluctuations. Reduces the penalty for over-hiring.

**--- Investment Costs ---**

*   `RND_COST_FACTOR = 600`
    *   **What it is:** A base factor determining the cost of R&D points. The actual cost per point also increases based on current quality and how low production cost already is (making later improvements more expensive).
    *   **Tweak Impact:**
        *   **Increase:** Makes R&D more expensive overall. Slows down technological progress (quality improvements, cost reductions).
        *   **Decrease:** Makes R&D cheaper overall. Speeds up technological progress.

*   `RND_POINTS_PER_UPGRADE = 120`
    *   **What it is:** How many R&D points are needed to trigger a breakthrough (choice to improve quality or reduce cost).
    *   **Tweak Impact:**
        *   **Increase:** Requires more R&D investment (and time) to achieve each upgrade. Slows down technological progress.
        *   **Decrease:** Allows for faster upgrades with less R&D spending per breakthrough. Speeds up technological progress.

*   `MARKETING_COST_FACTOR = 400`
    *   **What it is:** A base factor determining the cost to increase the marketing level. The cost increases significantly for higher levels (`level ** 1.5`).
    *   **Tweak Impact:**
        *   **Increase:** Makes increasing marketing levels more expensive, especially at higher levels.
        *   **Decrease:** Makes marketing levels cheaper to achieve.

**--- Finance/Loans ---**

*   `INTEREST_RATE = 0.50` (50% Annual)
    *   **What it is:** The *annual* interest rate earned on positive cash balances. This is divided by 12 and applied monthly. *(Note: 50% is extremely high for earning interest! Typical values might be 0.02 to 0.05 (2-5%)).*
    *   **Tweak Impact:**
        *   **Increase:** Rewards holding large cash balances more. Can become a significant income source if very high.
        *   **Decrease:** Reduces the benefit of holding cash. Encourages reinvesting money rather than saving.

*   `LOAN_INTEREST_RATE = 1.0` (100% Annual)
    *   **What it is:** The *annual* interest rate paid on outstanding loans. This is divided by 12 and applied monthly to the balance at the start of the period. *(Note: 100% is cripplingly high! Typical game values might be 0.08 to 0.20 (8-20%)).*
    *   **Tweak Impact:**
        *   **Increase:** Makes borrowing *very* expensive. Strongly discourages loans and makes escaping debt very difficult. Increases financial pressure significantly.
        *   **Decrease:** Makes borrowing cheaper. Loans become a more viable tool for funding growth or covering shortfalls. Reduces financial pressure from debt.

*   `MAX_LOAN_RATIO = 2.0`
    *   **What it is:** Determines the maximum loan amount allowed relative to the business's current assets (Cash + Inventory Value at Cost). A ratio of 2.0 means total loans cannot exceed 2 times the value of assets.
    *   **Tweak Impact:**
        *   **Increase:** Allows businesses to borrow more relative to their size. Can fuel faster growth but also increases risk of high debt.
        *   **Decrease:** Restricts borrowing capacity. Forces slower, more internally-funded growth and makes it harder to borrow out of trouble. Reduces maximum potential debt.

**General Advice for Tweaking:**

*   **Change one thing at a time:** Modify only one or two related variables, then playtest for a few turns to see the effect. Changing too much at once makes it hard to understand what caused the change in gameplay.
*   **Make small adjustments:** Double or halve values initially rather than making extreme 10x changes, unless you want a drastically different experience.
*   **Consider interactions:** Changing `BASE_DEMAND` affects how important the `SENSITIVITY` values are. Changing production costs affects the value of R&D.
*   **Think about difficulty:** Are you trying to make the game harder or easier? Faster or slower paced? More focused on production, finance, or R&D? Tailor your tweaks to your goal.
*   **Use Save/Load:** Save your game before making tweaks if you want to easily revert.