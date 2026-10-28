import random
import copy

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
    print(df.columns)
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

    # Simple cost model
    cost = energy * 0.2
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
        individual.house_size = max(30, min(300, individual.house_size))
    if random.random() < mutation_rate:
        individual.setpoint += random.uniform(-0.5, 0.5)
        individual.setpoint = max(15, min(30, individual.setpoint))
    if random.random() < mutation_rate:
        individual.hysteresis += random.uniform(-0.2, 0.2)
        individual.hysteresis = max(0.1, min(5.0, individual.hysteresis))
    if random.random() < mutation_rate:
        individual.heater_power += random.uniform(-1, 1)
        individual.heater_power = max(1, min(20, individual.heater_power))
    if random.random() < mutation_rate:
        individual.insulation = random.choice(["low", "medium", "high"])
    if random.random() < mutation_rate:
        individual.heater_type = random.choice(["electric", "gas", "heat_pump"])
    return individual

def gauss_mutate(individual, mutation_rate=0.5, sigma=1.0):
    if random.random() < mutation_rate:
        individual.house_size += random.gauss(0, sigma * 10)
        individual.house_size = max(30, min(300, individual.house_size))
    if random.random() < mutation_rate:
        individual.setpoint += random.gauss(0, sigma * 0.5)
        individual.setpoint = max(15, min(30, individual.setpoint))
    if random.random() < mutation_rate:
        individual.hysteresis += random.gauss(0, sigma * 0.2)
        individual.hysteresis = max(0.1, min(5.0, individual.hysteresis))
    if random.random() < mutation_rate:
        individual.heater_power += random.gauss(0, sigma * 1.0)
        individual.heater_power = max(1, min(20, individual.heater_power))
    # discrete variables stay random
    if random.random() < mutation_rate:
        individual.insulation = random.choice(["low", "medium", "high"])
    if random.random() < mutation_rate:
        individual.heater_type = random.choice(["electric", "gas", "heat_pump"])
    return individual

def GA(loop, ELITE_SIZE, mutation, mutation_rate, weather_data, obj):
    # initialize a random population
    population = initialize_population(50)
    best_individual = None

    # evolution Loop
    for generation in range(loop):
        sigma = 1 * (1 - generation / loop)  # mutation gets smaller over time (more exploration gives more exploitation)
        new_generation = []

        # choose objective
        if obj == "comfort":
            w1, w2, w3 = 1.5, 3.0, 1.0
        elif obj == "eco":
            w1, w2, w3 = 3.0, 1.5, 1.0
        elif obj == "budget":
            w1, w2, w3 = 1.0, 1.5, 3.0


        # 1. evaluate fitness
        for individual in population:
            energy, discomfort, cost = simulation(individual, weather_data)
            individual.fitness = calculate_fitness(energy, discomfort, cost, w1, w2, w3, len(weather_data))

        # 2. sort population and get the best
        population.sort(key=lambda ind: ind.fitness, reverse=True)
        best = population[0]
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

            # D. form new population
            new_generation.append(child)

        print(f"Gen {generation:3d} | "
              f"Size {best.house_size:6.2f} | "
              f"Ins {best.insulation:6s} | "
              f"Heat {best.heater_type:10s} | "
              f"Power {best.heater_power:6.4f} |"
              f"Fit {best.fitness:10.4f} | ")

        population = new_generation

    return best_individual

if __name__ == '__main__':
    weather_data = get_weather_data("open-meteo-63.16N14.69E312m.csv")
    print("Weather data")
    print(weather_data)
    best_individual= GA(30,
                        3,
                        "gauss_mutate",
                        0.6,
                        weather_data,
                        "eco")
    print("Best configurations:", best_individual)
