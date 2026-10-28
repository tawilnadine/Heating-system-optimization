import random
import copy
import matplotlib.pyplot as plt

class Individual:
    def __init__(self):
        self.house_size = random.uniform(50, 250)
        self.insulation = random.choice(["low", "medium", "high"])
        self.heater_type = random.choice(["electric", "gas", "heat_pump"])
        self.heater_power = random.uniform(2, 15)
        self.setpoint = random.uniform(18, 24)
        self.hysteresis = random.uniform(0.5, 3.0)
        self.fitness = None

    def __str__(self):
        return (f"size: {self.house_size}, "
                f"insulation: {self.insulation}, "
                f"heater type: {self.heater_type},"
                f" power: {self.heater_power}, "
                f"fitness: {self.fitness}")

def get_weather_data(file_name = "weather.csv", column = "temperature_2m (°C)"):
    import pandas as pd
    df = pd.read_csv(file_name, header=2)
    weather = df[column].values
    return weather

def initialize_population(size):
    return [Individual() for _ in range(size)]

def simulation(individual, weather_data):
    k = 0.001  # heat loss factor so temperature won't drop so fast
    temp_inside = 20
    heater_on = False
    energy = 0
    discomfort = 0

    insulation_map = {
        "low": 1.0,
        "medium": 0.6,
        "high": 0.3
    }
    insulation = insulation_map[individual.insulation]

    for temp in weather_data:
        temp_outside = temp

        #heat loss
        heat_loss = k * (temp_inside - temp_outside) * insulation * (individual.house_size ** 0.5)

        # Heater control
        if temp_inside < individual.setpoint - individual.hysteresis:
            heater_on = True
        elif temp_inside > individual.setpoint + individual.hysteresis:
            heater_on = False

        # Heat gain
        if heater_on:
            if individual.heater_type == "electric":
                heat_gain = individual.heater_power * 1.0
            elif individual.heater_type == "gas":
                heat_gain = individual.heater_power * 1.8
            elif individual.heater_type == "heat_pump":
                heat_gain = individual.heater_power * 3.5
        else:
            heat_gain = 0

        # Update temperature
        dt = 1  # 1 hour per step time scaling factor
        temp_inside = temp_inside + (heat_gain - heat_loss) * dt

        # Track metrics
        energy += heat_gain
        discomfort += abs(temp_inside - individual.setpoint)

    cost_map = {
        "electric": 1.5,
        "gas": 1.0,
        "heat_pump": 0.7
    }
    cost = energy * cost_map[individual.heater_type]

    return energy, discomfort, cost


def calculate_fitness(energy, discomfort, cost, w1, w2, w3, weather_data_lenght):
    fitness = -(w1 * energy + w2 * discomfort + w3 * cost)/weather_data_lenght
    return fitness

def select_parents(population, tournament_size=3):
    candidates = []
    for i in range(tournament_size):
        candidate = random.choice(population)
        candidates.append(candidate)
    candidates.sort(key=lambda ind: ind.fitness, reverse=True)  # sort by fitness (highest is best)
    parent1 = candidates[0]
    parent2 = candidates[1]
    return parent1, parent2

def crossover(parent1, parent2):
    child = Individual()
    child.house_size = random.choice([parent1.house_size, parent2.house_size])
    child.insulation = random.choice([parent1.insulation, parent2.insulation])
    child.heater_type = random.choice([parent1.heater_type, parent2.heater_type])
    child.heater_power = random.choice([parent1.heater_power, parent2.heater_power])
    child.setpoint = random.choice([parent1.setpoint, parent2.setpoint])
    child.hysteresis = random.choice([parent1.hysteresis, parent2.hysteresis])
    return child

def mutate(individual, mutation_rate=0.5):
    if random.random() < mutation_rate:
        individual.house_size += random.uniform(-10, 10)
    if random.random() < mutation_rate:
        individual.setpoint += random.uniform(-0.5, 0.5)
    if random.random() < mutation_rate:
        individual.hysteresis += random.uniform(-0.2, 0.2)
    if random.random() < mutation_rate:
        individual.heater_power += random.uniform(-1, 1)
    if random.random() < mutation_rate:
        individual.insulation = random.choice(["low", "medium", "high"])
    if random.random() < mutation_rate:
        individual.heater_type = random.choice(["electric", "gas", "heat_pump"])

    return individual


def gauss_mutate(individual, mutation_rate=0.5, sigma=1.0):
    if random.random() < mutation_rate:
        individual.house_size += random.gauss(0, sigma * 10)
    if random.random() < mutation_rate:
        individual.setpoint += random.gauss(0, sigma * 0.5)
    if random.random() < mutation_rate:
        individual.hysteresis += random.gauss(0, sigma * 0.2)
    if random.random() < mutation_rate:
        individual.heater_power += random.gauss(0, sigma * 1.0)
    # discrete variables stay random
    if random.random() < mutation_rate:
        individual.insulation = random.choice(["low", "medium", "high"])
    if random.random() < mutation_rate:
        individual.heater_type = random.choice(["electric", "gas", "heat_pump"])
    return individual

def population_stats(population):
    import numpy as np

    fitness_values = [ind.fitness for ind in population]
    sizes = [ind.house_size for ind in population]
    powers = [ind.heater_power for ind in population]

    # --- categorical counts (explicit & consistent) ---
    heater_counts = {
        "electric": 0,
        "gas": 0,
        "heat_pump": 0
    }

    insulation_counts = {
        "low": 0,
        "medium": 0,
        "high": 0
    }

    for ind in population:
        heater_counts[ind.heater_type] += 1
        insulation_counts[ind.insulation] += 1

    stats = {
        "fitness_mean": np.mean(fitness_values),
        "fitness_std": np.std(fitness_values),
        "fitness_best": max(fitness_values),
        "fitness_worst": min(fitness_values),

        "size_std": np.std(sizes),
        "power_std": np.std(powers),

        "heater_counts": heater_counts,
        "insulation_counts": insulation_counts
    }

    return stats

def diversity_score(population):
    unique = set(
        (round(ind.house_size,0),
         ind.insulation,
         ind.heater_type,
         round(ind.heater_power,))
        for ind in population
    )
    return len(unique) / len(population)


def plot_compare(stats3, stats4):
    gens3 = range(len(stats3))
    gens4 = range(len(stats4))

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    ax1, ax2, ax3 = axes

    # -------------------------
    # BEST FITNESS
    # -------------------------
    ax1.plot(gens3, [s["fitness_best"] for s in stats3], label="GA (LAB3)")
    ax1.plot(gens4, [s["fitness_best"] for s in stats4], label="Constrained GA (LAB4)")
    ax1.set_title("Best Fitness Comparison")
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Fitness")
    ax1.legend()
    ax1.grid()

    # -------------------------
    # MEAN FITNESS
    # -------------------------
    ax2.plot(gens3, [s["fitness_mean"] for s in stats3], label="GA (LAB3)")
    ax2.plot(gens4, [s["fitness_mean"] for s in stats4], label="Constrained GA (LAB4)")
    ax2.set_title("Mean Fitness Comparison")
    ax2.set_xlabel("Generation")
    ax2.set_ylabel("Fitness")
    ax2.legend()
    ax2.grid()

    # -------------------------
    # DIVERSITY
    # -------------------------
    ax3.plot(gens3, [s["diversity"] for s in stats3], label="GA (LAB3)")
    ax3.plot(gens4, [s["diversity"] for s in stats4], label="Constrained GA (LAB4)")
    ax3.set_title("Diversity Comparison")
    ax3.set_xlabel("Generation")
    ax3.set_ylabel("Diversity")
    ax3.legend()
    ax3.grid()

    plt.tight_layout()
    plt.show()



# *****************************************************************************
# *****************************************************************************
# *****************************************************************************
def clamp(individual):
    individual.house_size  = max(30,  min(250, individual.house_size))
    individual.heater_power = max(2,  min(15,  individual.heater_power))
    individual.setpoint    = max(18,  min(24,  individual.setpoint))
    individual.hysteresis  = max(0.5, min(3.0, individual.hysteresis))
    return individual

def is_valid(individual):
    # -------------------------------
    # RANGE CONSTRAINTS (continuous genes)
    # -------------------------------
    if not (30 <= individual.house_size <= 250):
        return False
    if not (2 <= individual.heater_power <= 15):
        return False
    if not (18 <= individual.setpoint <= 24):
        return False
    if not (0.5 <= individual.hysteresis <= 3.0):
        return False

    # -------------------------------
    # LOGICAL CONSTRAINTS
    # -------------------------------
    # Large house has high heat loss proportional to surface area.
    # If heating system is electric it cannot be under 6kW to maintain the setpoint temperature in  winter conditions.
    if individual.house_size > 180 and individual.heater_type == "electric" and individual.heater_power < 6:
        return False
    # Heat pumps require ground/air source installation space — not applicable for houses under 60m²
    if individual.heater_type == "heat_pump" and individual.house_size < 60:
        return False
    # Low insulation means high heat loss — no heater below 5kW can maintain setpoint in cold winter
    if individual.insulation == "low" and individual.heater_power < 5:
        return False

    return True

def replace_individual(population, mutation, mutation_rate, sigma):
    """
    Repair an invalid individual by mutating a valid one from the population.

    Strategy:
      1. Filter population to valid individuals only
      2. Pick a random valid candidate
      3. Mutate it until we get a valid result
      4. If stuck after 20 attempts, switch to a new candidate
      5. If stuck after MAX_TOTAL_ATTEMPTS, fall back to generate new Individual()
    """
    MAX_TOTAL_ATTEMPTS = 200

    valid_population = [ind for ind in population if is_valid(ind)]
    # safety fallback : if nobody is valid, generate fresh ones
    if len(valid_population) == 0:
        attempts = 0
        while True:
            ind = Individual()
            if is_valid(ind):
                return ind
            attempts += 1
            if attempts > MAX_TOTAL_ATTEMPTS:
                # Last resort : constraints may be contradictory
                raise RuntimeError("Could not generate a valid Individual after "
                                   f"{MAX_TOTAL_ATTEMPTS} attempts. "
                                   "Check your is_valid() constraints.")

    # sort by fitness to pick replacement candidate from top 33% only:
    evaluated = [ind for ind in valid_population if ind.fitness is not None]
    if evaluated:
        evaluated.sort(key=lambda ind: ind.fitness, reverse=True)

        # --- ADAPTIVE BIAS ---
        # sigma starts at 1.0 (early) and decays to 0.0 (late)
        # early: top 33% → exploit good solutions
        # late:  top 100% → explore freely, fight diversity collapse
        bias_fraction = 0.33 + (1.0 - 0.33) * (1.0 - sigma)
        top_cut = max(1, int(len(evaluated) * bias_fraction))
        top_valid = evaluated[:top_cut]
    else:
        top_valid = valid_population  # generation 0: no fitness yet


    candidate = copy.deepcopy(random.choice(top_valid))
    total_attempts = 0
    local_attempts = 0
    while total_attempts < MAX_TOTAL_ATTEMPTS:
        if mutation == "gauss_mutate":
            replacement = gauss_mutate(copy.deepcopy(candidate), mutation_rate, sigma)
        else:
            replacement = mutate(copy.deepcopy(candidate), mutation_rate)

        replacement = clamp(replacement)

        if is_valid(replacement):
            return replacement
        total_attempts += 1
        local_attempts += 1

        #  restart from population instead of recursion after 20
        if local_attempts > 20:
            candidate = copy.deepcopy(random.choice(top_valid))
            local_attempts = 0

    #  brute force a fresh valid individual after 200 attempts
    while True:
        ind = Individual()
        if is_valid(ind):
            return ind

def GA(population_size, loop, ELITE_SIZE, mutation, mutation_rate,
           weather_data, obj, mode="unconstrained"):
    all_stats = []
    # initialize a random population
    population = initialize_population(population_size)
    best_individual = None

    # evolution Loop
    for generation in range(loop):
        sigma = 1 * (1 - generation / loop)  # mutation gets smaller over time (more exploration gives more exploitation)
        new_generation = []

        # choose objective
        if obj == "comfort":
            w1, w2, w3 = 1.5, 2.0, 1.0
        elif obj == "eco":
            w1, w2, w3 = 2.0, 1.5, 1.0
        elif obj == "budget":
            w1, w2, w3 = 1.0, 1.5, 2.0


        # -------------------------------
        # LAB4 CONSTRAINT REPAIR STEP
        # -------------------------------
        if mode == "constrained":
            valid_population = []
            for individual in population:
                if is_valid(individual): valid_population.append(individual) # keep valid individual
                else: # replace invalid individual
                    new_ind = replace_individual(population, mutation, mutation_rate, sigma)
                    valid_population.append(new_ind)
            population = valid_population
        # -------------------------------

        # 1. evaluate fitness
        for individual in population:
            energy, discomfort, cost = simulation(individual, weather_data)
            individual.fitness = calculate_fitness(energy, discomfort, cost, w1, w2, w3, len(weather_data))

        # 2. sort population and get the best
        population.sort(key=lambda ind: ind.fitness, reverse=True)
        best = population[0]

        div = diversity_score(population)
        stats = population_stats(population)
        stats["diversity"] = div
        all_stats.append(stats)



        if best_individual is None or best.fitness > best_individual.fitness:
            best_individual = copy.deepcopy(best)

        # keep best individuals (elitism)
        for i in range(ELITE_SIZE):
            new_generation.append(population[i])


        # 2. build full new population
        for _ in range(len(population) - ELITE_SIZE):
            # A. choose parents
            parent1, parent2 = select_parents(population)

            # B. create children
            child = crossover(parent1, parent2)

            # C. mutate children
            if mutation == "gauss_mutate":
                child = gauss_mutate(child, mutation_rate, sigma)
            else:
                child = mutate(child, mutation_rate)

            # Repair immediately if constrained
            if mode == "constrained" and not is_valid(child):
                child = replace_individual(population, mutation, mutation_rate, sigma)

            # D. form new population
            new_generation.append(child)

        print(f"Gen {generation:3d} | "
              f"Best {best.fitness:8.4f} | "
              f"Mean {stats['fitness_mean']:8.4f} | "
              f"Std {stats['fitness_std']:8.4f} | "
              f"Heaters E:{stats['heater_counts']['electric']:2d} |"
              f"G:{stats['heater_counts']['gas']:2d} |"
              f"HP:{stats['heater_counts']['heat_pump']:2d} | "
              f"Ins L:{stats['insulation_counts']['low']:2d} |"
              f"M:{stats['insulation_counts']['medium']:2d} |"
              f"H:{stats['insulation_counts']['high']:2d} |"
              f"Diversity: {div:.2f}")


        population = new_generation

    return best_individual, all_stats

if __name__ == '__main__':
    weather_data = get_weather_data("open-meteo-63.16N14.69E312m.csv")
    population_size = 50
    loop = 30
    ELITE_SIZE = 2
    mutation_type = "gauss_mutate"
    mutation_rate = 0.8
    objective = "eco"
    best_individual3, stats3= GA(population_size,
                                loop,
                                ELITE_SIZE,
                                mutation_type,
                                mutation_rate,
                                weather_data,
                                objective)
    best_individual4, stats4= GA(population_size,
                                loop,
                                ELITE_SIZE,
                                mutation_type,
                                mutation_rate,
                                weather_data,
                                objective,
                                 "constrained")

    print("Best configurations (no constrains): ", best_individual3)
    print("Best configurations   (constrained): ", best_individual4)
    plot_compare(stats3, stats4)


