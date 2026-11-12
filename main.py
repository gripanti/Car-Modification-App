"""
ModMyRide - BMW Performance Calculator

A website that lets a BMW owner enter their car's stock numbers
(horsepower, weight, 0-60 time, top speed), pick modifications,
and see an estimate of how those mods change the car's performance.

The estimates use two simple ideas:
  * 0-60 time scales with the weight-to-power ratio (pounds per horsepower).
  * Top speed scales with the cube root of horsepower, because the power
    needed to push through air drag grows with speed cubed.
These are rough estimates, not actual results.

Tuning rules used by the site:
  * Only one tune can be installed at a time (Stage 1 OR Stage 2).
  * A Stage 2 tune is calibrated for a downpipe, so it requires one.
  * A downpipe only makes half its power without a tune, because the
    car's computer is not calibrated to use the extra exhaust flow.
"""
from dataclasses import dataclass
from drafter import *
from bakery import assert_equal


@dataclass
class Modification:
    """One upgrade that can be added onto the car."""
    name: str
    hp_gain: int
    weight_change: int
    selected: bool


@dataclass
class State:
    """Everything the website needs to remember between pages."""
    car_hp: int
    car_weight: int
    car_accel: float
    car_top: int
    selected_mods: list[Modification]
    mod_hp: int
    mod_hp_gain: int
    mod_weight: int
    mod_accel: float
    mod_top: int
    error_message: str

# Helper functions

def make_default_mods() -> list[Modification]:
    """Return a fresh list of the BMW modifications the site offers."""
    return [
        Modification("Cold Air Intake", 10, -5, False),
        Modification("Exhaust", 15, -20, False),
        Modification("Stage 1 Tune", 60, 0, False),
        Modification("Stage 2 Tune", 100, 0, False),
        Modification("Downpipe", 25, -10, False),
        Modification("Spark Plugs", 5, 0, False),
        Modification("Weight Reduction", 0, -100, False),
    ]


def make_starting_state() -> State:
    """Return a blank State with no car entered and no mods selected."""
    return State(0, 0, 0.0, 0, make_default_mods(), 0, 0, 0, 0.0, 0, "")


def make_field_name(mod_name: str) -> str:
    """Turn a modification name into the name used for its CheckBox."""
    return mod_name.lower().replace(" ", "_")

assert_equal(make_field_name("Cold Air Intake"), "cold_air_intake")
assert_equal(make_field_name("Stage 2 Tune"), "stage_2_tune")
assert_equal(make_field_name("Exhaust"), "exhaust")


def is_positive_number(text: str) -> bool:
    """Check that the text is a nonzero and positive number (decimals allowed)."""
    digits_only = text.strip().replace(".", "", 1)
    if not digits_only.isdigit():
        return False
    return float(text) > 0

assert_equal(is_positive_number("400"), True)
assert_equal(is_positive_number("4.2"), True)
assert_equal(is_positive_number("0"), False)
assert_equal(is_positive_number("-5"), False)
assert_equal(is_positive_number("fast"), False)
assert_equal(is_positive_number(""), False)


def is_mod_selected(mods: list[Modification], mod_name: str) -> bool:
    """Check whether the modification with the given name is selected."""
    for mod in mods:
        if mod.name == mod_name:
            return mod.selected
    return False

assert_equal(is_mod_selected(make_default_mods(), "Stage 1 Tune"), False)
assert_equal(is_mod_selected([Modification("Stage 1 Tune", 60, 0, True)],
                             "Stage 1 Tune"), True)
assert_equal(is_mod_selected([Modification("Exhaust", 15, -20, True)],
                             "Downpipe"), False)


def has_any_tune(mods: list[Modification]) -> bool:
    """Check whether either the Stage 1 or the Stage 2 tune is selected."""
    return (is_mod_selected(mods, "Stage 1 Tune")
            or is_mod_selected(mods, "Stage 2 Tune"))

assert_equal(has_any_tune(make_default_mods()), False)
assert_equal(has_any_tune([Modification("Stage 2 Tune", 100, 0, True)]),
             True)


def count_selected(mods: list[Modification]) -> int:
    """Count how many modifications the user has selected."""
    total = 0
    for mod in mods:
        if mod.selected:
            total = total + 1
    return total

assert_equal(count_selected(make_default_mods()), 0)
assert_equal(count_selected([Modification("Exhaust", 15, -20, True),
                             Modification("Spark Plugs", 5, 0, False)]), 1)


def check_mod_choices(mods: list[Modification]) -> str:
    """
    Check the selected mods against the tuning rules. Return an error
    message describing the problem, or an empty string if everything is good.
    """
    if count_selected(mods) == 0:
        return "Please select at least one modification."
    if (is_mod_selected(mods, "Stage 1 Tune")
            and is_mod_selected(mods, "Stage 2 Tune")):
        return "Please pick only one tune: Stage 1 or Stage 2."
    if (is_mod_selected(mods, "Stage 2 Tune")
            and not is_mod_selected(mods, "Downpipe")):
        return "A Stage 2 tune requires a downpipe."
    return ""

assert_equal(check_mod_choices(make_default_mods()),
             "Please select at least one modification.")
assert_equal(check_mod_choices([Modification("Stage 1 Tune", 60, 0, True),
                                Modification("Stage 2 Tune", 100, 0, True),
                                Modification("Downpipe", 25, -10, True)]),
             "Please pick only one tune: Stage 1 or Stage 2.")
assert_equal(check_mod_choices([Modification("Stage 2 Tune", 100, 0, True),
                                Modification("Downpipe", 25, -10, False)]),
             "A Stage 2 tune requires a downpipe.")
assert_equal(check_mod_choices([Modification("Stage 2 Tune", 100, 0, True),
                                Modification("Downpipe", 25, -10, True)]),
             "")


def total_hp_gain(mods: list[Modification]) -> int:
    """
    Add up the horsepower gain of every selected modification.
    A downpipe only gives half its gain without a tune.
    """
    tuned = has_any_tune(mods)
    total = 0
    for mod in mods:
        if mod.selected:
            if mod.name == "Downpipe" and not tuned:
                total = total + mod.hp_gain // 2
            else:
                total = total + mod.hp_gain
    return total

assert_equal(total_hp_gain(make_default_mods()), 0)
assert_equal(total_hp_gain([Modification("Downpipe", 25, -10, True)]), 12)
assert_equal(total_hp_gain([Modification("Downpipe", 25, -10, True),
                            Modification("Stage 1 Tune", 60, 0, True)]), 85)
assert_equal(total_hp_gain([Modification("Downpipe", 25, -10, True),
                            Modification("Stage 2 Tune", 100, 0, True)]), 125)


def total_weight_change(mods: list[Modification]) -> int:
    """Add up the weight change of every selected modification.
       Weight is given in pounds.
    """
    total = 0
    for mod in mods:
        if mod.selected:
            total = total + mod.weight_change
    return total

assert_equal(total_weight_change(make_default_mods()), 0)
assert_equal(total_weight_change([Modification("Exhaust", 15, -20, True),
                                  Modification("Weight Reduction", 0, -100,
                                               True)]), -120)


def power_to_weight(hp: int, weight: int) -> float:
    """
    Return horsepower per ton, rounded to one decimal place.
    A ton is 2,000 pounds.
    """
    if weight <= 0:
        return 0.0
    return round(hp / weight * 2000, 1)

assert_equal(power_to_weight(400, 4000), 200.0)
assert_equal(power_to_weight(510, 3965), 257.3)
assert_equal(power_to_weight(400, 0), 0.0)


def estimate_zero_to_sixty(old_time: float, old_hp: int, old_weight: int,
                           new_hp: int, new_weight: int) -> float:
    """
    Scale the stock 0-60 time by how much the pounds-per-horsepower
    ratio changed. Rounded to two decimal places.
    The engineering priciple [ 1/2 * m * v² = P * t  ->  t = m * v² / (2P) ] is used to calulate the time.
    """
    old_ratio = old_weight / old_hp
    new_ratio = new_weight / new_hp
    return round(old_time * new_ratio / old_ratio, 2)

assert_equal(estimate_zero_to_sixty(4.0, 400, 4000, 400, 4000), 4.0)
assert_equal(estimate_zero_to_sixty(4.0, 400, 4000, 500, 4000), 3.2)
assert_equal(estimate_zero_to_sixty(4.0, 400, 4000, 510, 3965), 3.11)


def estimate_top_speed(old_top: int, old_hp: int, new_hp: int) -> int:
    """
    Estimate the new top speed. Drag power grows with speed cubed, so
    speed grows with the cube root of power: ** (1 / 3) is a cube root.
    """
    return round(old_top * (new_hp / old_hp) ** (1 / 3))

assert_equal(estimate_top_speed(155, 400, 400), 155)
assert_equal(estimate_top_speed(100, 100, 800), 200)
assert_equal(estimate_top_speed(155, 400, 510), 168)


def selected_mod_names(mods: list[Modification]) -> list[str]:
    """Return the names of the selected modifications."""
    names = []
    for mod in mods:
        if mod.selected:
            names.append(mod.name)
    return names

assert_equal(selected_mod_names(make_default_mods()), [])
assert_equal(selected_mod_names([Modification("Exhaust", 15, -20, True),
                                 Modification("Spark Plugs", 5, 0, False)]),
                                 ["Exhaust"])


def describe_mod(mod: Modification) -> str:
    """Return a short label for a modification's checkbox."""
    return (mod.name + " (+" + str(mod.hp_gain) + " hp, "
            + str(mod.weight_change) + " lb)")

assert_equal(describe_mod(Modification("Exhaust", 15, -20, False)),
             "Exhaust (+15 hp, -20 lb)")
assert_equal(describe_mod(Modification("Stage 2 Tune", 100, 0, False)),
             "Stage 2 Tune (+100 hp, 0 lb)")


def performance_verdict(state: State) -> str:
    """Compare stock and modified 0-60 times and describe the result."""
    if state.mod_accel < state.car_accel:
        saved = round(state.car_accel - state.mod_accel, 2)
        return ("Your build is quicker! It should hit 60 MPH about "
                + str(saved) + " seconds sooner.")
    return "These mods are not expected to make your car any quicker."

# Tests for performance_verdict are below, after the test states are made.


# Routes

@route
def index(state: State) -> Page:
    """Home page: introduces ModMyRide."""
    return Page(state, [
        Header("ModMyRide"),
        "The BMW Performance Calculator",
        "Enter your car's stock numbers, choose your mods, and see an "
        "estimate of your new horsepower, power-to-weight ratio, "
        "0-60 time, and top speed.",
        Button("Get Started", car_input_page),
    ])


@route
def car_input_page(state: State) -> Page:
    """Input page: the user types in the car's stock performance numbers.
       The user is also given the option to moive tpo the next page of go back home.
    """
    content = [Header("Enter Your Car's Stock Stats", 2)]
    if state.error_message != "":
        content.append("Error: " + state.error_message)
    content.extend([
        "Horsepower:", TextBox("horsepower", str(state.car_hp)),
        "Weight (lb):", TextBox("weight", str(state.car_weight)),
        "0-60 MPH time (seconds):",
        TextBox("zero_to_sixty", str(state.car_accel)),
        "Top speed (MPH):", TextBox("top_speed", str(state.car_top)),
        Button("Next: Choose Mods", save_car_stats),
        Button("Back to Home", index),
    ])
    return Page(state, content)


@route
def save_car_stats(state: State, horsepower: str, weight: str,
                   zero_to_sixty: str, top_speed: str) -> Page:
    """
    Check the four stock values. If any is not a positive number, show the
    input page again with an error. If everything checks out, save them and move on.
    """
    if not (is_positive_number(horsepower) and is_positive_number(weight)
            and is_positive_number(zero_to_sixty)
            and is_positive_number(top_speed)):
        state.error_message = ("All four values must be positive numbers. "
                               "Please try again.")
        return car_input_page(state)
    state.car_hp = round(float(horsepower))
    state.car_weight = round(float(weight))
    state.car_accel = float(zero_to_sixty)
    state.car_top = round(float(top_speed))
    state.error_message = ""
    return modification_page(state)


@route
def modification_page(state: State) -> Page:
    """Modification page: one CheckBox for each available upgrade.
       The user will have the option to calculate the performace results or go back to car stats.
    """
    content = [Header("Choose Your Modifications", 2)]
    if state.error_message != "":
        content.append("Error: " + state.error_message)
    content.append("Tips: pick only one tune. A Stage 2 tune requires a "
                   "downpipe, and a downpipe only makes full power with "
                   "a tune.")
    for mod in state.selected_mods:
        content.append(CheckBox(make_field_name(mod.name), mod.selected))
        content.append(describe_mod(mod))
    content.append(Button("Calculate Results", select_modification))
    content.append(Button("Back to Car Stats", car_input_page))
    return Page(state, content)


@route
def select_modification(state: State, cold_air_intake: bool, exhaust: bool,
                        stage_1_tune: bool, stage_2_tune: bool,
                        downpipe: bool, spark_plugs: bool,
                        weight_reduction: bool) -> Page:
    """
    Save which checkboxes were ticked. If the choices break a tuning rule,
    send the user back to the modification page with an error. If not, calculate the results.
    """
    """
    A dictionary is used here. Drafter passes each checkbox in as its own True/False parameter.
    To copy those values onto the matching Modification objects, this
    dictionary pairs each checkbox's name with whether it was ticked.
    For example, choices["exhaust"] gives back the value of the
    exhaust parameter. The loop below turns each mod's name into its checkbox name with
    make_field_name (ex. "Cold Air Intake" -> "cold_air_intake"),
    looks that name up in the dictionary, and saves the True/False result in mod.selected.
    """
    choices = {"cold_air_intake": cold_air_intake, "exhaust": exhaust,
               "stage_1_tune": stage_1_tune, "stage_2_tune": stage_2_tune,
               "downpipe": downpipe, "spark_plugs": spark_plugs,
               "weight_reduction": weight_reduction}
    for mod in state.selected_mods:
        mod.selected = choices[make_field_name(mod.name)]
    problem = check_mod_choices(state.selected_mods)
    if problem != "":
        state.error_message = problem
        return modification_page(state)
    state.error_message = ""
    return calculate_performance(state)


@route
def calculate_performance(state: State) -> Page:
    """Calculate every modified value from the stock values and the mods."""
    state.mod_hp_gain = total_hp_gain(state.selected_mods)
    state.mod_hp = state.car_hp + state.mod_hp_gain
    state.mod_weight = (state.car_weight
                        + total_weight_change(state.selected_mods))
    state.mod_accel = estimate_zero_to_sixty(state.car_accel, state.car_hp,
                                             state.car_weight, state.mod_hp,
                                             state.mod_weight)
    state.mod_top = estimate_top_speed(state.car_top, state.car_hp,
                                       state.mod_hp)
    return results_page(state)


@route
def results_page(state: State) -> Page:
    """Results page: a stock vs. modified comparison table."""
    return Page(state, [
        Header("Your Estimated Results", 2),
        Table([
            ["Stat", "Stock", "Modified"],
            ["Horsepower", str(state.car_hp), str(state.mod_hp)],
            ["Weight (lb)", str(state.car_weight), str(state.mod_weight)],
            ["Power-to-weight (hp per ton)",
             str(power_to_weight(state.car_hp, state.car_weight)),
             str(power_to_weight(state.mod_hp, state.mod_weight))],
            ["0-60 MPH (s)", str(state.car_accel), str(state.mod_accel)],
            ["Top speed (MPH)", str(state.car_top), str(state.mod_top)],
        ]),
        "Horsepower gained: +" + str(state.mod_hp_gain) + " hp",
        performance_verdict(state),
        "Selected mods:",
        BulletedList(selected_mod_names(state.selected_mods)),
        Button("Change Mods", modification_page),
        Button("Start Over", reset_page),
    ])


@route
def reset_page(state: State) -> Page:
    """
    Start-over page: asks the user to confirm if they want to clear
    everything and return to the home page.
    """
    return Page(state, [
        Header("Start Over?", 2),
        "This clears your car's stats and every selected modification.",
        Button("Yes, Start a New Build", start_over),
        Button("No, Back to Results", results_page),
    ])


@route
def start_over(state: State) -> Page:
    """Reset the State to a blank build and go back to the home page."""
    return index(make_starting_state())

# Route tests

def make_test_state() -> State:
    """Return a State with a 400 hp, 4,000 lb car entered and no mods."""
    return State(400, 4000, 4.0, 155, make_default_mods(), 0, 0, 0, 0.0, 0,
                 "")


def make_stage_1_state() -> State:
    """Return the test car with intake, exhaust, Stage 1 and downpipe."""
    mods = make_default_mods()
    mods[0].selected = True
    mods[1].selected = True
    mods[2].selected = True
    mods[4].selected = True
    return State(400, 4000, 4.0, 155, mods, 510, 110, 3965, 3.11, 168, "")


def make_stage_2_state() -> State:
    """Return the test car with intake, exhaust, Stage 2 and downpipe."""
    mods = make_default_mods()
    mods[0].selected = True
    mods[1].selected = True
    mods[3].selected = True
    mods[4].selected = True
    return State(400, 4000, 4.0, 155, mods, 550, 150, 3965, 2.88, 172, "")


# performance_verdict test
assert_equal(performance_verdict(make_stage_1_state()),
             "Your build is quicker! It should hit 60 MPH about "
             "0.89 seconds sooner.")
no_gain_state = make_test_state()
no_gain_state.mod_accel = 4.0
assert_equal(performance_verdict(no_gain_state),
             "These mods are not expected to make your car any quicker.")

# index
assert_equal(index(make_starting_state()), Page(make_starting_state(), [
    Header("ModMyRide"),
    "The BMW Performance Calculator",
    "Enter your car's stock numbers, choose your mods, and see an "
    "estimate of your new horsepower, power-to-weight ratio, "
    "0-60 time, and top speed.",
    Button("Get Started", car_input_page),
]))

# car_input_page: header, 4 labels, 4 text boxes, 2 buttons
assert_equal(car_input_page(make_test_state()).state, make_test_state())
assert_equal(len(car_input_page(make_test_state()).content), 11)

# save_car_stats: good input moves on and stores the numbers
assert_equal(save_car_stats(make_starting_state(), "400", "4000", "4.0",
                            "155").state, make_test_state())
# save_car_stats: bad input stays put and sets an error
bad_input_state = make_starting_state()
bad_input_state.error_message = ("All four values must be positive "
                                 "numbers. Please try again.")
assert_equal(save_car_stats(make_starting_state(), "abc", "4000", "4.0",
                            "155").state, bad_input_state)

# modification_page: header, tip, 2 items per mod (7 mods), 2 buttons
assert_equal(len(modification_page(make_test_state()).content), 18)
assert_equal(modification_page(make_test_state()).state, make_test_state())

# select_modification: Stage 1 build
assert_equal(select_modification(make_test_state(), True, True, True, False,
                                 True, False, False).state,
             make_stage_1_state())
# select_modification: Stage 2 build
assert_equal(select_modification(make_test_state(), True, True, False, True,
                                 True, False, False).state,
             make_stage_2_state())
# select_modification: nothing chosen gives an error
no_mods_state = make_test_state()
no_mods_state.error_message = "Please select at least one modification."
assert_equal(select_modification(make_test_state(), False, False, False,
                                 False, False, False, False).state,
             no_mods_state)
# select_modification: Stage 2 without a downpipe gives an error
no_downpipe_state = make_test_state()
no_downpipe_state.selected_mods[3].selected = True
no_downpipe_state.error_message = "A Stage 2 tune requires a downpipe."
assert_equal(select_modification(make_test_state(), False, False, False,
                                 True, False, False, False).state,
             no_downpipe_state)

# calculate_performance
stage_2_choices_only = make_stage_2_state()
stage_2_choices_only.mod_hp = 0
stage_2_choices_only.mod_hp_gain = 0
stage_2_choices_only.mod_weight = 0
stage_2_choices_only.mod_accel = 0.0
stage_2_choices_only.mod_top = 0
assert_equal(calculate_performance(stage_2_choices_only).state,
             make_stage_2_state())

# results_page
assert_equal(results_page(make_stage_1_state()).state, make_stage_1_state())
assert_equal(len(results_page(make_stage_1_state()).content), 8)

# reset_page
assert_equal(reset_page(make_stage_1_state()), Page(make_stage_1_state(), [
    Header("Start Over?", 2),
    "This clears your car's stats and every selected modification.",
    Button("Yes, Start a New Build", start_over),
    Button("No, Back to Results", results_page),
]))

# start_over
assert_equal(start_over(make_stage_2_state()).state, make_starting_state())


set_site_information(
    author="Grayden Ripanti",
    description="ModMyRide estimates how modifications change a \
                BMW's horsepower, power-to-weight ratio, 0-60 time, \
                and top speed.",
    sources=["Drafter documentation", "Bakery textbook", "Claude LLM"],
    planning=["Ripanti CS1 Final Project 0: Pick a Problem", "Ripanti CS1 Final Project 1: Design"],
    links=["https://github.com/gripanti/Car-Modification-App/"]
)
start_server(make_starting_state())
