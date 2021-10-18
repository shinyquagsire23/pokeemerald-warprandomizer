from pathlib import Path
import os

import json
import networkx as nx
import matplotlib.pyplot as plt
import random
import threading
import time

# Starting seed to search from
rand_idx = 126794

# For searching, the found seed
found_seed = -1
threads = []
num_threads = 0

if "POKEEMERALD" not in os.environ or os.environ["POKEEMERALD"] is None:
    print("Please set POKEEMERALD environment variable to our pokeemerald directory path")
    print ("Exiting...")
    exit(-1)

pokeemerald_dir = os.environ["POKEEMERALD"]
mapdata_dir = os.path.join(pokeemerald_dir, "data/maps/")

# Read map groups
f_map_groups = open(os.path.join(mapdata_dir, "map_groups.json"), "r")
data_map_groups = json.load(f_map_groups)
f_map_groups.close()

# Maps with only one door
map_deadends = []
map_numdoors = {}

map_require_multidoors = [
    "MAP_RUSTBORO_CITY_GYM", "MAP_GRANITE_CAVE_STEVENS_ROOM", "MAP_RUSTBORO_CITY_DEVON_CORP_3F",
    "MAP_METEOR_FALLS_1F_1R", "MAP_MT_PYRE_SUMMIT", "MAP_SLATEPORT_CITY_STERNS_SHIPYARD_1F", "MAP_SLATEPORT_CITY_OCEANIC_MUSEUM_2F",
    "MAP_MAUVILLE_CITY_HOUSE1", "MAP_MAUVILLE_CITY_GYM", "MAP_ROUTE119_WEATHER_INSTITUTE_2F", "MAP_DEWFORD_TOWN_GYM",
]

# TODO: whitelist for ie MAP_MOSSDEEP_CITY_GYM entrance?
map_donot_edit = [
    "MAP_NONE",
    "MAP_TERRA_CAVE_ENTRANCE",
    "MAP_TERRA_CAVE_END",

    "MAP_LITTLEROOT_TOWN"
    #"MAP_FIERY_PATH",
    "MAP_PETALBURG_WOODS",
    "MAP_LAVARIDGE_TOWN_GYM_1F",
    "MAP_LAVARIDGE_TOWN_GYM_B1F",
    "MAP_SOOTOPOLIS_CITY_GYM_1F",
    "MAP_SOOTOPOLIS_CITY_GYM_B1F",
    "MAP_EVER_GRANDE_CITY_HALL5",
    "MAP_EVER_GRANDE_CITY_HALL4",
    "MAP_EVER_GRANDE_CITY_HALL3",
    "MAP_EVER_GRANDE_CITY_HALL2",
    "MAP_EVER_GRANDE_CITY_HALL1",
    "MAP_EVER_GRANDE_CITY_SIDNEYS_ROOM",
    "MAP_EVER_GRANDE_CITY_PHOEBES_ROOM",
    "MAP_EVER_GRANDE_CITY_GLACIAS_ROOM",
    "MAP_EVER_GRANDE_CITY_DRAKES_ROOM",
    "MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM",
    "MAP_ROUTE110_TRICK_HOUSE_PUZZLE1",
    "MAP_ROUTE110_TRICK_HOUSE_PUZZLE2",
    "MAP_ROUTE110_TRICK_HOUSE_PUZZLE3",
    "MAP_ROUTE110_TRICK_HOUSE_PUZZLE4",
    "MAP_ROUTE110_TRICK_HOUSE_PUZZLE5",
    "MAP_ROUTE110_TRICK_HOUSE_PUZZLE6",
    "MAP_ROUTE110_TRICK_HOUSE_PUZZLE7",
    "MAP_ROUTE110_TRICK_HOUSE_PUZZLE8",
    "MAP_ROUTE110_TRICK_HOUSE_ENTRANCE",
    "MAP_ROUTE110_TRICK_HOUSE_END",
    "MAP_ROUTE110_TRICK_HOUSE_CORRIDOR",
    "MAP_ANCIENT_TOMB", "MAP_ISLAND_CAVE", "MAP_DESERT_RUINS",
    "MAP_MOSSDEEP_CITY_GYM", # TODO: this would be an extra level of hell if implemented, but have to verify the puzzle too
    "MAP_SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM",
    "MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM",
    "MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM",
    "MAP_SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM",
    "MAP_SHOAL_CAVE_HIGH_TIDE_ENTRANCE_ROOM",
    "MAP_SHOAL_CAVE_HIGH_TIDE_INNER_ROOM",
    "MAP_PETALBURG_CITY_GYM", # The exit warps are funky
    "MAP_SCORCHED_SLAB", # Easy softlock, also a dead end anyhow
    "MAP_TRAINER_HILL_1F",
    "MAP_TRAINER_HILL_2F",
    "MAP_TRAINER_HILL_3F",
    "MAP_TRAINER_HILL_4F",
    "MAP_TRAINER_HILL_ROOF",
    "MAP_TRAINER_HILL_ELEVATOR",
]

mapwarp_donot_edit = [
    "MAP_PETALBURG_CITY_GYM_WARP0",
    "MAP_PETALBURG_CITY_GYM_WARP1",
    "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP5", # Locked
    "MAP_TRAINER_HILL_ENTRANCE_WARP2",
    "MAP_SLATEPORT_CITY_HARBOR_WARP2",
    "MAP_SLATEPORT_CITY_HARBOR_WARP3",
]

map_exclusion_list = [
    "MAP_NONE",
    "MAP_UNION_ROOM",
    "MAP_TRADE_CENTER",
    "MAP_SOOTOPOLIS_CITY_MYSTERY_EVENTS_HOUSE_B1F",
]

# Bidirectional manual linking
# This is usually required for places like the route with Petalburg Woods, 
# Normann's gym and teleport puzzles, where there's distinct partitioning
# and we can't assume every warp can reach every other warp.
# 
# This also gets used for Mr. Briney
map_manual_links_bidir = [
    ("MAP_ROUTE104_MR_BRINEYS_HOUSE", "MAP_DEWFORD_TOWN"),
    
    ("MAP_ROUTE109", "MAP_DEWFORD_TOWN"),
    ("MAP_JAGGED_PASS", "MAP_ROUTE112_WARP2"),
    
    ("MAP_ROUTE111_WARP0", "MAP_ROUTE111"),
    ("MAP_ROUTE111_WARP4", "MAP_ROUTE111"),
    
    ("MAP_ROUTE112_WARP2", "MAP_LAVARIDGE_TOWN"),
    ("MAP_ROUTE112_WARP3", "MAP_LAVARIDGE_TOWN"),
    ("MAP_ROUTE112_WARP0", "MAP_ROUTE112"),
    ("MAP_ROUTE112_WARP1", "MAP_ROUTE112"),
    ("MAP_ROUTE112_WARP4", "MAP_ROUTE112"),
    ("MAP_ROUTE111_WARP2", "MAP_ROUTE113"),
    ("MAP_ROUTE112_WARP5", "MAP_ROUTE113"),
    
    ("MAP_ROUTE111_WARP4", "MAP_ROUTE111"),
    ("MAP_ROUTE111_WARP0", "MAP_ROUTE111"),
    
    ("MAP_MT_CHIMNEY_CABLE_CAR_STATION", "MAP_ROUTE112_CABLE_CAR_STATION"),
    
    ("MAP_UNDERWATER_SEAFLOOR_CAVERN", "MAP_SEAFLOOR_CAVERN_ENTRANCE"),
    ("MAP_UNDERWATER_SOOTOPOLIS_CITY", "MAP_SOOTOPOLIS_CITY"),
    
    ("MAP_ROUTE104", "MAP_ROUTE104_WARP4"),
    ("MAP_ROUTE104", "MAP_ROUTE104_WARP5"),
    ("MAP_ROUTE104", "MAP_ROUTE104_WARP6"),
    ("MAP_ROUTE104", "MAP_ROUTE104_WARP7"),
    ("MAP_ROUTE104", "MAP_ROUTE104_WARP0"),
    
    ("MAP_ROUTE104_WARP1", "MAP_RUSTBORO_CITY"),
    ("MAP_ROUTE104_WARP2", "MAP_RUSTBORO_CITY"),
    ("MAP_ROUTE104_WARP3", "MAP_RUSTBORO_CITY"),
    
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP0", "MAP_LAVARIDGE_TOWN_GYM_1F"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP0", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP2"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP0", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP3"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP7", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP5"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP4", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP6"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP6", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP10"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP10", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP11"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP13", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP16"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP16", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP14"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP14", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP15"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP18", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP19"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP19", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP20"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP22", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP23"),
    
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP2", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP3"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP3", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP1"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP1", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP6"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP6", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP8"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP8", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP7"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP11", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP9"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP9", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP10"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP13", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP5"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP17", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP2"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP14", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP15"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP15", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP16"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP16", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP19"),
    
    ("MAP_PETALBURG_CITY_GYM_WARP0", "MAP_PETALBURG_CITY_GYM"),
    ("MAP_PETALBURG_CITY_GYM_WARP0", "MAP_PETALBURG_CITY_GYM_WARP2"),
    ("MAP_PETALBURG_CITY_GYM_WARP0", "MAP_PETALBURG_CITY_GYM_WARP5"),
    ("MAP_PETALBURG_CITY_GYM_WARP6", "MAP_PETALBURG_CITY_GYM_WARP14"),
    ("MAP_PETALBURG_CITY_GYM_WARP3", "MAP_PETALBURG_CITY_GYM_WARP9"),
    ("MAP_PETALBURG_CITY_GYM_WARP3", "MAP_PETALBURG_CITY_GYM_WARP8"),
    ("MAP_PETALBURG_CITY_GYM_WARP18", "MAP_PETALBURG_CITY_GYM_WARP23"),
    ("MAP_PETALBURG_CITY_GYM_WARP3", "MAP_PETALBURG_CITY_GYM_WARP9"),
    ("MAP_PETALBURG_CITY_GYM_WARP12", "MAP_PETALBURG_CITY_GYM_WARP21"),
    ("MAP_PETALBURG_CITY_GYM_WARP16", "MAP_PETALBURG_CITY_GYM_WARP22"),
    ("MAP_PETALBURG_CITY_GYM_WARP12", "MAP_PETALBURG_CITY_GYM_WARP16"),
    ("MAP_PETALBURG_CITY_GYM_WARP21", "MAP_PETALBURG_CITY_GYM_WARP22"),
    ("MAP_PETALBURG_CITY_GYM_WARP10", "MAP_PETALBURG_CITY_GYM_WARP20"),
    ("MAP_PETALBURG_CITY_GYM_WARP30", "MAP_PETALBURG_CITY_GYM_WARP28"),
    ("MAP_PETALBURG_CITY_GYM_WARP28", "MAP_PETALBURG_CITY_GYM_WARP33"),
    ("MAP_PETALBURG_CITY_GYM_WARP21", "MAP_PETALBURG_CITY_GYM_WARP22"),
    ("MAP_PETALBURG_CITY_GYM_WARP24", "MAP_PETALBURG_CITY_GYM_WARP26"),
    ("MAP_PETALBURG_CITY_GYM_WARP26", "MAP_PETALBURG_CITY_GYM_WARP32"),
    
    ("MAP_ROUTE116_WARP2", "MAP_ROUTE116_WARP4"),
    
    # Bike
    ("MAP_ROUTE110_WARP3", "MAP_ROUTE110_WARP5"),
    
    # Sootopolis is split by water
    ("MAP_SOOTOPOLIS_CITY_WARP0", "MAP_SOOTOPOLIS_CITY"), # PC <-> lake
    ("MAP_SOOTOPOLIS_CITY_WARP0", "MAP_SOOTOPOLIS_CITY_WARP12"),
    ("MAP_SOOTOPOLIS_CITY_WARP12", "MAP_SOOTOPOLIS_CITY_WARP9"),
    ("MAP_SOOTOPOLIS_CITY_WARP9", "MAP_SOOTOPOLIS_CITY_WARP11"),
    ("MAP_SOOTOPOLIS_CITY_WARP11", "MAP_SOOTOPOLIS_CITY_WARP7"),
    ("MAP_SOOTOPOLIS_CITY_WARP7", "MAP_SOOTOPOLIS_CITY_WARP5"),
    
    ("MAP_SOOTOPOLIS_CITY_WARP2", "MAP_SOOTOPOLIS_CITY"), # Gym <-> lake
    
    ("MAP_SOOTOPOLIS_CITY_WARP1", "MAP_SOOTOPOLIS_CITY"), # Mart -> lake
    ("MAP_SOOTOPOLIS_CITY_WARP1", "MAP_SOOTOPOLIS_CITY_WARP10"),
    ("MAP_SOOTOPOLIS_CITY_WARP10", "MAP_SOOTOPOLIS_CITY_WARP8"),
    ("MAP_SOOTOPOLIS_CITY_WARP8", "MAP_SOOTOPOLIS_CITY_WARP6"),
    ("MAP_SOOTOPOLIS_CITY_WARP6", "MAP_SOOTOPOLIS_CITY_WARP4"),
    ("MAP_SOOTOPOLIS_CITY_WARP4", "MAP_SOOTOPOLIS_CITY_WARP3"),
    
    # Aqua hideout is teleport hell
    ("MAP_AQUA_HIDEOUT_B2F_WARP8", "MAP_AQUA_HIDEOUT_B2F_WARP9"),
    ("MAP_AQUA_HIDEOUT_B2F_WARP0", "MAP_AQUA_HIDEOUT_B2F_WARP3"),
    ("MAP_AQUA_HIDEOUT_B2F_WARP3", "MAP_AQUA_HIDEOUT_B2F_WARP6"),
    ("MAP_AQUA_HIDEOUT_B2F_WARP1", "MAP_AQUA_HIDEOUT_B2F_WARP4"),
    ("MAP_AQUA_HIDEOUT_B2F_WARP2", "MAP_AQUA_HIDEOUT_B2F_WARP5"),
    
    ("MAP_AQUA_HIDEOUT_B1F_WARP2", "MAP_AQUA_HIDEOUT_B1F_WARP3"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP1", "MAP_AQUA_HIDEOUT_B1F_WARP6"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP0", "MAP_AQUA_HIDEOUT_B1F_WARP5"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP5", "MAP_AQUA_HIDEOUT_B1F_WARP4"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP8", "MAP_AQUA_HIDEOUT_B1F_WARP9"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP9", "MAP_AQUA_HIDEOUT_B1F_WARP10"),
    
    # Big Master Ball puzzle -- TODO will this sort itself out?
    ("MAP_AQUA_HIDEOUT_B1F_WARP12", "MAP_AQUA_HIDEOUT_B1F_WARP13"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP13", "MAP_AQUA_HIDEOUT_B1F_WARP14"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP14", "MAP_AQUA_HIDEOUT_B1F_WARP15"),
    
    ("MAP_AQUA_HIDEOUT_B1F_WARP16", "MAP_AQUA_HIDEOUT_B1F_WARP17"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP17", "MAP_AQUA_HIDEOUT_B1F_WARP18"),
    
    ("MAP_AQUA_HIDEOUT_B1F_WARP19", "MAP_AQUA_HIDEOUT_B1F_WARP20"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP20", "MAP_AQUA_HIDEOUT_B1F_WARP21"),
    
    ("MAP_AQUA_HIDEOUT_B1F_WARP22", "MAP_AQUA_HIDEOUT_B1F_WARP23"),
    ("MAP_AQUA_HIDEOUT_B1F_WARP23", "MAP_AQUA_HIDEOUT_B1F_WARP24"),
    
    ("MAP_SEAFLOOR_CAVERN_ROOM5_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM5_WARP2"),
    
    # Abandoned ship corridors
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP2", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP3"),
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP3", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP8"),
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP8", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP10"),
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP10", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP11"),
    
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP0", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP1"),
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP1", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP4"),
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP4", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP5"),
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP5", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP6"),
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP6", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP7"),
    ("MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP7", "MAP_ABANDONED_SHIP_CORRIDORS_1F_WARP9"),
    
    ("MAP_ABANDONED_SHIP_HIDDEN_FLOOR_ROOMS_WARP7", "MAP_ABANDONED_SHIP_HIDDEN_FLOOR_ROOMS_WARP8"),
    
    ("MAP_ABANDONED_SHIP_DECK_WARP3", "MAP_ABANDONED_SHIP_DECK_WARP4"),
    
    # Meteor falls
    ("MAP_METEOR_FALLS_1F_2R_WARP1", "MAP_METEOR_FALLS_1F_2R_WARP2"),
    
    ("MAP_METEOR_FALLS_B1F_1R_WARP3", "MAP_METEOR_FALLS_B1F_1R_WARP5"),
    ("MAP_METEOR_FALLS_B1F_1R_WARP5", "MAP_METEOR_FALLS_B1F_1R_WARP1"),
    
    ("MAP_METEOR_FALLS_B1F_1R_WARP0", "MAP_METEOR_FALLS_B1F_1R_WARP2"),
    ("MAP_METEOR_FALLS_B1F_1R_WARP2", "MAP_METEOR_FALLS_B1F_1R_WARP4"),
    
    ("MAP_VICTORY_ROAD_1F_WARP1", "MAP_VICTORY_ROAD_1F_WARP2"),
    ("MAP_VICTORY_ROAD_B1F_WARP1", "MAP_VICTORY_ROAD_B1F_WARP6"),
    ("MAP_VICTORY_ROAD_B1F_WARP5", "MAP_VICTORY_ROAD_B1F_WARP6"),
    
    ("MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM_WARP2", "MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM"),
    
    ("MAP_GRANITE_CAVE_1F_WARP3", "MAP_GRANITE_CAVE_1F_WARP1"),
    ("MAP_JAGGED_PASS_WARP2", "MAP_JAGGED_PASS_WARP3"), 
    
    ("MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM_WARP2", "MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM_WARP3"),
    
    ("MAP_SKY_PILLAR_4F_WARP2", "MAP_SKY_PILLAR_4F_WARP1"),
    
    ("MAP_RUSTURF_TUNNEL_WARP0", "MAP_RUSTURF_TUNNEL_WARP1"),
    ("MAP_RUSTURF_TUNNEL_WARP1", "MAP_RUSTURF_TUNNEL_WARP2"),
    
    ("MAP_EVER_GRANDE_CITY_WARP3", "MAP_EVER_GRANDE_CITY_WARP0"),
    
    ("MAP_LILYCOVE_CITY_DEPARTMENT_STORE_ELEVATOR", "MAP_LILYCOVE_CITY_DEPARTMENT_STORE_1F"),
    ("MAP_LILYCOVE_CITY_DEPARTMENT_STORE_ELEVATOR", "MAP_LILYCOVE_CITY_DEPARTMENT_STORE_2F"),
    ("MAP_LILYCOVE_CITY_DEPARTMENT_STORE_ELEVATOR", "MAP_LILYCOVE_CITY_DEPARTMENT_STORE_3F"),
    ("MAP_LILYCOVE_CITY_DEPARTMENT_STORE_ELEVATOR", "MAP_LILYCOVE_CITY_DEPARTMENT_STORE_4F"),
    ("MAP_LILYCOVE_CITY_DEPARTMENT_STORE_ELEVATOR", "MAP_LILYCOVE_CITY_DEPARTMENT_STORE_5F"),
    ("MAP_LILYCOVE_CITY_DEPARTMENT_STORE_ELEVATOR", "MAP_LILYCOVE_CITY_DEPARTMENT_STORE_ROOFTOP"),
    
    # TODO All The Ledges
]

# Monodirectional manual linking
# Usually used for maps which have ledges, ie Jagged Pass
map_manual_links_monodir = [
    ("MAP_ROUTE112_WARP2", "MAP_ROUTE112"), # ledges, one direction
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP5", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP4"),
    ("MAP_LAVARIDGE_TOWN_GYM_1F_WARP25", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP0"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP18", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP23"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP23", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP0"),
    ("MAP_LAVARIDGE_TOWN_GYM_B1F_WARP21", "MAP_LAVARIDGE_TOWN_GYM_B1F_WARP0"),
    ("MAP_SEAFLOOR_CAVERN_ROOM5_WARP1", "MAP_SEAFLOOR_CAVERN_ROOM5_WARP0"),
    ("MAP_SEAFLOOR_CAVERN_ROOM5_WARP2", "MAP_SEAFLOOR_CAVERN_ROOM5_WARP3"),
    
    ("MAP_METEOR_FALLS_1F_2R_WARP1", "MAP_METEOR_FALLS_1F_2R_WARP3"), # Ledges
    ("MAP_GRANITE_CAVE_1F_WARP3", "MAP_GRANITE_CAVE_1F"),
    ("MAP_GRANITE_CAVE_B2F_WARP3", "MAP_GRANITE_CAVE_B2F_WARP2"), 
    
    ("MAP_JAGGED_PASS_WARP2", "MAP_JAGGED_PASS_WARP4"),
    ("MAP_JAGGED_PASS_WARP3", "MAP_JAGGED_PASS_WARP4"),
    
    ("MAP_JAGGED_PASS_WARP2", "MAP_JAGGED_PASS_WARP0"),
    ("MAP_JAGGED_PASS_WARP2", "MAP_JAGGED_PASS_WARP1"),
    ("MAP_JAGGED_PASS_WARP3", "MAP_JAGGED_PASS_WARP0"),
    ("MAP_JAGGED_PASS_WARP3", "MAP_JAGGED_PASS_WARP1"),
    
    ("MAP_JAGGED_PASS_WARP4", "MAP_JAGGED_PASS_WARP0"),
    ("MAP_JAGGED_PASS_WARP4", "MAP_JAGGED_PASS_WARP1"),
    
    ("MAP_SKY_PILLAR_4F", "MAP_SKY_PILLAR_3F_WARP2"), # Floor falling
    ("MAP_SKY_PILLAR_4F_WARP2", "MAP_SKY_PILLAR_3F_WARP0"), # Floor falling
    
    ("MAP_MIRAGE_TOWER_3F", "MAP_MIRAGE_TOWER_2F_WARP0"),
]

# Maps which definitely need warps linked manually
# (ie, MAP_ROUTE112_WARP0 will not be linked to MAP_ROUTE112 unless done manually)
map_nomapnode = [
    "MAP_PETALBURG_CITY_GYM",
    "MAP_LAVARIDGE_TOWN_GYM_1F", "MAP_LAVARIDGE_TOWN_GYM_B1F",
    "MAP_ROUTE104", "MAP_ROUTE112", "MAP_ROUTE111", "MAP_SOOTOPOLIS_CITY",
    "MAP_SEAFLOOR_CAVERN_ROOM5", "MAP_AQUA_HIDEOUT_B1F", "MAP_AQUA_HIDEOUT_B2F",
    "MAP_ABANDONED_SHIP_CORRIDORS_1F", "MAP_ABANDONED_SHIP_ROOMS_1F",
    "MAP_ABANDONED_SHIP_ROOMS_B1F", "MAP_ABANDONED_SHIP_HIDDEN_FLOOR_ROOMS",
    "MAP_METEOR_FALLS_B1F_1R", "MAP_JAGGED_PASS", "MAP_RUSTURF_TUNNEL",
]

# Bidirectional unlinks
# Usually used for map connections which are purely aesthetic
# and cannot be crossed by the player
map_manual_unlinks_bidir = [
    ("MAP_ROUTE114", "MAP_ROUTE115"),
    ("MAP_ROUTE112", "MAP_ROUTE113"),
    ("MAP_ROUTE112", "MAP_LAVARIDGE_TOWN"),
    ("MAP_JAGGED_PASS", "MAP_ROUTE112"),
    ("MAP_SLATEPORT_CITY", "MAP_ROUTE134"),
    ("MAP_ROUTE122", "MAP_ROUTE123"),
    ("MAP_ROUTE104", "MAP_RUSTBORO_CITY"),
    ("MAP_ROUTE111", "MAP_ROUTE113"),
    ("MAP_VERDANTURF_TOWN", "MAP_ROUTE116"),
    ("MAP_ROUTE116_WARP2", "MAP_ROUTE116"),
    ("MAP_ROUTE116_WARP4", "MAP_ROUTE116"),
    
    # Bike
    ("MAP_ROUTE110_WARP3", "MAP_ROUTE110"),
    ("MAP_ROUTE110_WARP5", "MAP_ROUTE110"),
    
    ("MAP_ABANDONED_SHIP_ROOMS_1F_WARP2", "MAP_ABANDONED_SHIP_ROOMS_1F"),
    ("MAP_METEOR_FALLS_1F_1R_WARP3", "MAP_METEOR_FALLS_1F_1R"),
    ("MAP_METEOR_FALLS_1F_1R_WARP4", "MAP_METEOR_FALLS_1F_1R"),
    ("MAP_METEOR_FALLS_1F_1R_WARP5", "MAP_METEOR_FALLS_1F_1R"),
    ("MAP_METEOR_FALLS_1F_2R_WARP1", "MAP_METEOR_FALLS_1F_2R"),
    ("MAP_METEOR_FALLS_1F_2R_WARP2", "MAP_METEOR_FALLS_1F_2R"),
    
    ("MAP_VICTORY_ROAD_1F_WARP1", "MAP_VICTORY_ROAD_1F"),
    ("MAP_VICTORY_ROAD_1F_WARP2", "MAP_VICTORY_ROAD_1F"),
    ("MAP_VICTORY_ROAD_1F_WARP3", "MAP_VICTORY_ROAD_1F"),
    
    ("MAP_VICTORY_ROAD_B1F_WARP3", "MAP_VICTORY_ROAD_B1F"),
    ("MAP_VICTORY_ROAD_B1F_WARP1", "MAP_VICTORY_ROAD_B1F"),
    ("MAP_VICTORY_ROAD_B1F_WARP5", "MAP_VICTORY_ROAD_B1F"),
    ("MAP_VICTORY_ROAD_B1F_WARP6", "MAP_VICTORY_ROAD_B1F"),
    
    ("MAP_ABANDONED_SHIP_DECK_WARP3", "MAP_ABANDONED_SHIP_DECK"),
    ("MAP_ABANDONED_SHIP_DECK_WARP4", "MAP_ABANDONED_SHIP_DECK"),
    
    ("MAP_GRANITE_CAVE_1F_WARP1", "MAP_GRANITE_CAVE_1F"),
    ("MAP_GRANITE_CAVE_1F_WARP3", "MAP_GRANITE_CAVE_1F"), 
    
    ("MAP_GRANITE_CAVE_B2F_WARP2", "MAP_GRANITE_CAVE_B2F"), 
    ("MAP_GRANITE_CAVE_B2F_WARP3", "MAP_GRANITE_CAVE_B2F"), 
    ("MAP_GRANITE_CAVE_B2F_WARP4", "MAP_GRANITE_CAVE_B2F"), 
    
    ("MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM_WARP4", "MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM"),
    ("MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM_WARP6", "MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM"),
    ("MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM_WARP2", "MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM"),
    ("MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM_WARP3", "MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM"),
    
    ("MAP_SKY_PILLAR_4F_WARP2", "MAP_SKY_PILLAR_4F"),
    ("MAP_SKY_PILLAR_4F_WARP1", "MAP_SKY_PILLAR_4F"),
    
    ("MAP_SKY_PILLAR_3F_WARP2", "MAP_SKY_PILLAR_3F"),
    
    ("MAP_EVER_GRANDE_CITY_WARP0", "MAP_EVER_GRANDE_CITY"),
    ("MAP_EVER_GRANDE_CITY_WARP3", "MAP_EVER_GRANDE_CITY"),
]

# Monodirectional unlinks.
# Helpful for cleaning up maps where some warps are isolated or have ledges.
map_manual_unlinks_mono = [
    ("MAP_MAGMA_HIDEOUT_1F", "MAP_MAGMA_HIDEOUT_1F_WARP3"),
    ("MAP_MAGMA_HIDEOUT_1F", "MAP_MAGMA_HIDEOUT_1F_WARP2"),
    ("MAP_METEOR_FALLS_1F_1R_WARP3", "MAP_METEOR_FALLS_1F_1R_WARP5"), # Steven's cave
    ("MAP_MT_PYRE_1F_WARP5", "MAP_MT_PYRE_2F_WARP4"), # holes in Mt Pyre are one-way
    ("MAP_MT_PYRE_2F_WARP2", "MAP_MT_PYRE_3F_WARP4"),
    ("MAP_MT_PYRE_2F_WARP3", "MAP_MT_PYRE_3F_WARP5"),
    ("MAP_MT_PYRE_3F_WARP2", "MAP_MT_PYRE_4F_WARP4"),
    ("MAP_MT_PYRE_3F_WARP3", "MAP_MT_PYRE_4F_WARP5"),
    ("MAP_MT_PYRE_4F_WARP2", "MAP_MT_PYRE_5F_WARP3"),
    ("MAP_MT_PYRE_4F_WARP3", "MAP_MT_PYRE_5F_WARP4"),
    ("MAP_MT_PYRE_5F_WARP2", "MAP_MT_PYRE_6F_WARP1"),
]

# Add attributes to bidirectional edges
# Sometimes this is a story requirement (ie, Mr. Briney requires Peeko to be saved)
# and sometimes it's just a barrier (ie Strength is needed to go from one warp to another)
map_bidir_edge_attributes = [
    [("MAP_ROUTE103", "MAP_ROUTE110"), {"requires": ["surf"]}],
    [("MAP_ROUTE104", "MAP_PETALBURG_CITY"), {"requires": ["wally"]}],
    [("MAP_ROUTE104", "MAP_ROUTE105"), {"requires": ["surf"]}],
    [("MAP_ROUTE105", "MAP_ROUTE106"), {"requires": ["surf"]}],
    
    [("MAP_ROUTE103", "MAP_ROUTE103_WARP0"), {"requires": ["surf"]}], # altering cave
    
    [("MAP_ROUTE116", "MAP_ROUTE116_WARP1"), {"requires": ["savepeeko"]}],
    [("MAP_RUSTURF_TUNNEL_WARP0", "MAP_RUSTURF_TUNNEL_WARP1"), {"requires": ["savepeeko", "rocksmash"]}],
    [("MAP_ROUTE104_MR_BRINEYS_HOUSE", "MAP_DEWFORD_TOWN"), {"requires": ["savepeeko"]}],
    
    [("MAP_DEWFORD_TOWN", "MAP_ROUTE109"), {"requires": ["letter"]}],
    [("MAP_ROUTE107", "MAP_ROUTE108"), {"requires": ["surf"]}],
    [("MAP_ROUTE108", "MAP_ROUTE109"), {"requires": ["surf"]}],
    
    # Aqua grunts blocking the warp
    [("MAP_SLATEPORT_CITY", "MAP_SLATEPORT_CITY_WARP5"), {"requires": ["sterngoods"]}],
    [("MAP_SLATEPORT_CITY", "MAP_SLATEPORT_CITY_WARP7"), {"requires": ["sterngoods"]}],

    # Aqua grunts blocking the route
    [("MAP_SLATEPORT_CITY", "MAP_ROUTE110"), {"requires": ["museum"]}],
    
    # Bike entrance
    [("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE_WARP0", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE"), {"requires": ["bike"]}],
    [("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE_WARP1", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE"), {"requires": ["bike"]}],
    [("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE_WARP2", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE"), {"requires": ["bike"]}],
    [("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE_WARP3", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE"), {"requires": ["bike"]}],
    
    # Bike entrance 2
    [("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE_WARP0", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE"), {"requires": ["bike"]}],
    [("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE_WARP1", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE"), {"requires": ["bike"]}],
    [("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE_WARP2", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE"), {"requires": ["bike"]}],
    [("MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE_WARP3", "MAP_ROUTE110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE"), {"requires": ["bike"]}],

    # New Mauville entrance
    [("MAP_ROUTE110", "MAP_ROUTE110_WARP0"), {"requires": ["surf"]}],
    
    # Boulders blocking
    [("MAP_MAUVILLE_CITY", "MAP_ROUTE111"), {"requires": ["rocksmash"]}],
    
    # Magma grunts blocking the way
    [("MAP_ROUTE112_WARP0", "MAP_ROUTE112_CABLE_CAR_STATION_WARP0"), {"requires": ["meteorite"]}],
    [("MAP_ROUTE112_WARP1", "MAP_ROUTE112_CABLE_CAR_STATION_WARP1"), {"requires": ["meteorite"]}],
    [("MAP_ROUTE112_WARP0", "MAP_ROUTE112"), {"requires": ["meteorite"]}],
    [("MAP_ROUTE112_WARP1", "MAP_ROUTE112"), {"requires": ["meteorite"]}],
    
    [("MAP_MAUVILLE_CITY", "MAP_ROUTE118"), {"requires": ["surf"]}],
    
    # Grunts blocking
    [("MAP_ROUTE119", "MAP_FORTREE_CITY"), {"requires": ["weatherinst"]}],
    
    # Kecleon
    [("MAP_FORTREE_CITY", "MAP_FORTREE_CITY_GYM"), {"requires": ["scope"]}],
    
    [("MAP_ROUTE120", "MAP_SCORCHED_SLAB"), {"requires": ["surf"]}],
    [("MAP_ROUTE121", "MAP_ROUTE122"), {"requires": ["surf"]}],
    
    # Aqua is blocking this connection
    [("MAP_LILYCOVE_CITY", "MAP_ROUTE124"), {"requires": ["aquagone"]}],
    
    # Magma hideout
    [("MAP_JAGGED_PASS_WARP4", "MAP_JAGGED_PASS_WARP0"), {"requires": ["magmaemblem"]}],
    [("MAP_JAGGED_PASS_WARP4", "MAP_JAGGED_PASS_WARP1"), {"requires": ["magmaemblem"]}],
    [("MAP_JAGGED_PASS_WARP2", "MAP_JAGGED_PASS_WARP4"), {"requires": ["magmaemblem"]}],
    [("MAP_JAGGED_PASS_WARP3", "MAP_JAGGED_PASS_WARP4"), {"requires": ["magmaemblem"]}],
    [("MAP_MAGMA_HIDEOUT_1F_WARP0", "MAP_MAGMA_HIDEOUT_1F"), {"requires": ["strength"]}],
    [("MAP_MAGMA_HIDEOUT_1F", "MAP_MAGMA_HIDEOUT_2F_1R"), {"requires": ["strength"]}],
    [("MAP_MAGMA_HIDEOUT_1F", "MAP_MAGMA_HIDEOUT_2F_3R"), {"requires": ["strength"]}],
    
    # Aqua guards
    [("MAP_AQUA_HIDEOUT_1F_WARP0", "MAP_AQUA_HIDEOUT_1F_WARP2"), {"requires": ["magmadone", "aquasub"]}],
    [("MAP_AQUA_HIDEOUT_1F_WARP1", "MAP_AQUA_HIDEOUT_1F_WARP2"), {"requires": ["magmadone", "aquasub"]}],
    
    # Bunch of surf connections
    [("MAP_ROUTE124", "MAP_ROUTE126"), {"requires": ["surf"]}],
    [("MAP_ROUTE124", "MAP_ROUTE125"), {"requires": ["surf"]}],
    [("MAP_ROUTE125", "MAP_MOSSDEEP_CITY"), {"requires": ["surf"]}],
    [("MAP_ROUTE124", "MAP_MOSSDEEP_CITY"), {"requires": ["surf"]}],
    
    [("MAP_MOSSDEEP_CITY", "MAP_ROUTE127"), {"requires": ["surf"]}],
    [("MAP_ROUTE127", "MAP_ROUTE128"), {"requires": ["surf"]}],
    [("MAP_ROUTE128", "MAP_ROUTE129"), {"requires": ["surf"]}],
    [("MAP_ROUTE129", "MAP_ROUTE130"), {"requires": ["surf"]}],
    [("MAP_ROUTE130", "MAP_ROUTE131"), {"requires": ["surf"]}],
    [("MAP_ROUTE131", "MAP_PACIFIDLOG_TOWN"), {"requires": ["surf"]}],
    [("MAP_PACIFIDLOG_TOWN", "MAP_ROUTE132"), {"requires": ["surf"]}],
    [("MAP_ROUTE132", "MAP_ROUTE133"), {"requires": ["surf"]}],
    [("MAP_ROUTE133", "MAP_ROUTE134"), {"requires": ["surf"]}],
    
    # All dive spots
    [("MAP_ROUTE124", "MAP_UNDERWATER_ROUTE124"), {"requires": ["surf", "dive"]}],
    [("MAP_ROUTE126", "MAP_UNDERWATER_ROUTE126"), {"requires": ["surf", "dive"]}],
    [("MAP_ROUTE127", "MAP_UNDERWATER_ROUTE127"), {"requires": ["surf", "dive"]}],
    [("MAP_ROUTE128", "MAP_UNDERWATER_ROUTE128"), {"requires": ["surf", "dive"]}],
    [("MAP_ROUTE129", "MAP_UNDERWATER_ROUTE129"), {"requires": ["surf", "dive"]}],
    [("MAP_ROUTE105", "MAP_UNDERWATER_ROUTE105"), {"requires": ["surf", "dive"]}],
    [("MAP_ROUTE125", "MAP_UNDERWATER_ROUTE125"), {"requires": ["surf", "dive"]}],
    
    # Map script?
    [("MAP_UNDERWATER_SEAFLOOR_CAVERN", "MAP_SEAFLOOR_CAVERN_ENTRANCE"), {"requires": ["surf", "dive"]}],
    
    # TODO more specific here
    [("MAP_SEAFLOOR_CAVERN_ROOM1_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM1_WARP1"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM1_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM1_WARP2"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM2_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM2"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM2_WARP1", "MAP_SEAFLOOR_CAVERN_ROOM2"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM2_WARP2", "MAP_SEAFLOOR_CAVERN_ROOM2"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM2_WARP3", "MAP_SEAFLOOR_CAVERN_ROOM2"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM5_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM5"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM5_WARP1", "MAP_SEAFLOOR_CAVERN_ROOM5"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM5_WARP2", "MAP_SEAFLOOR_CAVERN_ROOM5"), {"requires": ["strength", "rocksmash"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM6_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM6"), {"requires": ["surf"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM6_WARP1", "MAP_SEAFLOOR_CAVERN_ROOM6"), {"requires": ["surf"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM6_WARP2", "MAP_SEAFLOOR_CAVERN_ROOM6"), {"requires": ["surf"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM7_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM7"), {"requires": ["surf"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM7_WARP1", "MAP_SEAFLOOR_CAVERN_ROOM7"), {"requires": ["surf"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM8_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM8"), {"requires": ["strength"]}],
    [("MAP_SEAFLOOR_CAVERN_ROOM8_WARP0", "MAP_SEAFLOOR_CAVERN_ROOM8"), {"requires": ["strength"]}],
    
    # Sky pillar doesn't appear until later
    [("MAP_ROUTE131", "MAP_ROUTE131_WARP0"), {"requires": ["spicyweatherwallace"]}],
    [("MAP_SKY_PILLAR_OUTSIDE_WARP0", "MAP_SKY_PILLAR_OUTSIDE_WARP1"), {"requires": ["spicyweatherwallace"]}],
    [("MAP_SKY_PILLAR_TOP_WARP0", "MAP_SKY_PILLAR_TOP"), {"requires": ["spicyweatherwallace"]}],
    
    # Can't enter the gym until the weather is done and you talk to leaders
    [("MAP_SOOTOPOLIS_CITY", "MAP_SOOTOPOLIS_CITY_WARP0"), {"requires": ["surf"]}], # Lake -> PC
    [("MAP_SOOTOPOLIS_CITY_WARP2", "MAP_SOOTOPOLIS_CITY"), {"requires": ["surf", "dive", "spicyweatherwallace", "talkleaders"]}], # Lake -> Gym
    [("MAP_SOOTOPOLIS_CITY", "MAP_SOOTOPOLIS_CITY_WARP1"), {"requires": ["surf"]}], # Lake -> Mart
    
    [("MAP_SOOTOPOLIS_CITY_WARP4", "MAP_SOOTOPOLIS_CITY_WARP3"), {"requires": ["dive"]}], # House -> Cave of origin entrance
    

    # Evergrande requires waterfall to enter
    [("MAP_ROUTE128", "MAP_EVER_GRANDE_CITY"), {"requires": ["waterfall"]}],
    
    # TODO: More specific on these
    [("MAP_VICTORY_ROAD_B1F_WARP5", "MAP_VICTORY_ROAD_B1F_WARP6"), {"requires": ["rocksmash", "strength"]}],
    [("MAP_VICTORY_ROAD_B1F_WARP4", "MAP_VICTORY_ROAD_B1F"), {"requires": ["rocksmash", "strength"]}],
    [("MAP_VICTORY_ROAD_B1F_WARP0", "MAP_VICTORY_ROAD_B1F"), {"requires": ["rocksmash", "strength"]}],
    [("MAP_VICTORY_ROAD_B1F_WARP2", "MAP_VICTORY_ROAD_B1F"), {"requires": ["rocksmash", "strength"]}],
    
    [("MAP_VICTORY_ROAD_B2F_WARP0", "MAP_VICTORY_ROAD_B2F"), {"requires": ["surf", "waterfall", "rocksmash", "strength"]}],
    [("MAP_VICTORY_ROAD_B2F_WARP1", "MAP_VICTORY_ROAD_B2F"), {"requires": ["surf", "waterfall", "rocksmash", "strength"]}],
    [("MAP_VICTORY_ROAD_B2F_WARP2", "MAP_VICTORY_ROAD_B2F"), {"requires": ["surf", "waterfall", "rocksmash", "strength"]}],
    [("MAP_VICTORY_ROAD_B2F_WARP3", "MAP_VICTORY_ROAD_B2F"), {"requires": ["surf", "waterfall", "rocksmash", "strength"]}],
    
    [("MAP_EVER_GRANDE_CITY_POKEMON_LEAGUE_1F_WARP2", "MAP_EVER_GRANDE_CITY_HALL5_WARP0"), {"requires": ["waterfall"]}],
    [("MAP_EVER_GRANDE_CITY_POKEMON_LEAGUE_1F_WARP3", "MAP_EVER_GRANDE_CITY_HALL5_WARP0"), {"requires": ["waterfall"]}],
    
    [("MAP_ROUTE111_WARP3", "MAP_ROUTE111"), {"requires": ["goggles"]}],
    [("MAP_ROUTE111_WARP1", "MAP_ROUTE111"), {"requires": ["goggles"]}],
    
    [("MAP_ROUTE115", "MAP_ROUTE115_WARP0"), {"requires": ["surf"]}],
    [("MAP_ROUTE115", "MAP_ROUTE115_WARP1"), {"requires": ["surf"]}], # Terra cave
    [("MAP_ROUTE115", "MAP_ROUTE115_WARP2"), {"requires": ["surf"]}], # Terra cave
    
    # Gym won't open until Brawley is beaten
    [("MAP_PETALBURG_CITY_GYM_WARP0", "MAP_PETALBURG_CITY_GYM_WARP2"), {"requires": ["goggles", "flash"]}],
    [("MAP_PETALBURG_CITY_GYM_WARP0", "MAP_PETALBURG_CITY_GYM_WARP5"), {"requires": ["goggles", "flash"]}],
    
    [("MAP_ROUTE114", "MAP_ROUTE114_WARP4"), {"requires": ["surf", "waterfall"]}], # Terra cave
    [("MAP_ROUTE105_WARP0", "MAP_ROUTE105"), {"requires": ["surf"]}], # regi cave
    [("MAP_ROUTE108_WARP0", "MAP_ROUTE108"), {"requires": ["surf"]}], # abandoned ship
    
    [("MAP_METEOR_FALLS_1F_1R_WARP2", "MAP_METEOR_FALLS_1F_1R"), {"requires": ["surf", "waterfall"]}],
    
    [("MAP_METEOR_FALLS_B1F_1R_WARP3", "MAP_METEOR_FALLS_B1F_1R_WARP5"), {"requires": ["surf"]}],
    [("MAP_METEOR_FALLS_B1F_1R_WARP5", "MAP_METEOR_FALLS_B1F_1R_WARP1"), {"requires": ["surf"]}],
    
    [("MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM_WARP3", "MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM"), {"requires": ["strength"]}],
    
    [("MAP_GRANITE_CAVE_B1F_WARP4", "MAP_GRANITE_CAVE_B1F"), {"requires": ["bike"]}],
    [("MAP_GRANITE_CAVE_B1F_WARP5", "MAP_GRANITE_CAVE_B1F"), {"requires": ["bike"]}],
    [("MAP_GRANITE_CAVE_B1F_WARP6", "MAP_GRANITE_CAVE_B1F"), {"requires": ["bike"]}],
    
    # Guy blocking the entrance
    [("MAP_RUSTBORO_CITY_DEVON_CORP_3F_WARP2", "MAP_RUSTBORO_CITY_DEVON_CORP_3F"), {"requires": ["savepeeko"]}],
    
    [("MAP_MIRAGE_TOWER_2F_WARP0", "MAP_MIRAGE_TOWER_2F"), {"requires": ["bike"]}],
    [("MAP_MIRAGE_TOWER_2F_WARP1", "MAP_MIRAGE_TOWER_2F"), {"requires": ["bike"]}],
    
    [("MAP_MIRAGE_TOWER_3F_WARP0", "MAP_MIRAGE_TOWER_3F"), {"requires": ["rocksmash"]}],
    [("MAP_MIRAGE_TOWER_3F_WARP1", "MAP_MIRAGE_TOWER_3F"), {"requires": ["rocksmash"]}],
]

map_list = []
map_id_to_folder = {}
map_folder_to_id = {}
num_warps = 0

G = nx.DiGraph()

#G.add_node("MAP_ROUTE112_JAGGED")

# Find all map jsons
paths = sorted(Path(mapdata_dir).glob('**/map.json'))
for path in paths:
    map_path = str(path)
    
    map_list += [map_path]
    
    # Do thing with the path
    #print(map_path)

# One more pass to do some misc mappings
for m in map_list:
    f = open(m, "r")
    data = json.load(f)
    f.close()
    
    map_rel_path = os.path.relpath(m, mapdata_dir)
    
    m_id = data["id"]
    dirname = os.path.dirname(map_rel_path)
    
    # Store the map ID -> folder mapping
    map_id_to_folder[m_id] = dirname
    map_folder_to_id[dirname] = m_id
    
    if "UNUSED" in m_id or "BATTLE_FRONTIER" in m_id or "BATTLE_TENT" in m_id:
        map_exclusion_list += [m_id]
    
    if "LITTLEROOT" in m_id or "BATTLE_TENT" in m_id:
        map_donot_edit += [m_id]

# Exclude all indoor dynamic maps
for m in data_map_groups["gMapGroup_IndoorDynamic"]:
    map_exclusion_list += [map_folder_to_id[m]]

# Build the full graph
for m in map_list:
    f = open(m, "r")
    data = json.load(f)
    f.close()
    
    m_id = data["id"]
    if m_id in map_exclusion_list:
        continue
    G.add_node(m_id)
    
    # Every warp is a one-way edge
    if "warp_events" in data:
        warps = data["warp_events"]
        w_idx = 0
        w_id_list = []
        dest_maps = []
        for warp in warps:
            w_id = m_id + "_WARP" + str(w_idx)
            dest_map = warp["dest_map"]
            w_id_dest = dest_map + "_WARP" + str(warp["dest_warp_id"])
            
            if dest_map not in map_exclusion_list:
                G.add_edge(w_id, w_id_dest, t="warp", requires=[])
            
            if m_id not in map_nomapnode:
                G.add_edge(w_id, m_id, t="connection", requires=[])
                G.add_edge(m_id, w_id, t="connection", requires=[])
            dest_maps += [w_id_dest]
            w_idx += 1

        dest_maps = set(dest_maps)
        map_numdoors[m_id] = len(dest_maps)
        if len(dest_maps) == 1 and (data["connections"] is None or len(data["connections"]) == 0):
            map_deadends += [m_id]
        #print (w_id, len(warps))
    
    # Every connection is a two-way edge
    cons = data["connections"]
    if cons is None:
        continue
    
    for con in cons:
        G.add_edge(m_id, con["map"], t="connection", requires=[])
        G.add_edge(con["map"], m_id, t="connection", requires=[])

print (map_deadends)

# Add manual links
for v in map_manual_links_monodir:
    G.add_edge(v[0], v[1], t="connection", requires=[])

for v in map_manual_links_bidir:
    con_type = "connection"
    #if "_WARP" in v[0] and "_WARP" in v[1]:
    #    con_type = "warp"
    G.add_edge(v[0], v[1], t=con_type, requires=[])
    G.add_edge(v[1], v[0], t=con_type, requires=[])

# Manual unlinks
for v in map_manual_unlinks_bidir:
    try:
        G.remove_edge(v[0], v[1])
    except:
        a = "a"
    try:
        G.remove_edge(v[1], v[0])
    except:
        a = "a"

for v in map_manual_unlinks_mono:
    try:
        G.remove_edge(v[0], v[1])
    except:
        a = "a"

# Find all bidirectional warps and one-way warps
biconnections = set()
oneway_connections = set()
def have_bidirectional_relationship(G, node1, node2):
    return G.has_edge(node1, node2) and G.has_edge(node2, node1)

for u,v,a in G.edges(data=True):
    if u > v:  # Avoid duplicates, such as (1, 2) and (2, 1)
        v, u = u, v
    if have_bidirectional_relationship(G, u, v) and a["t"] == "warp":
        biconnections.add((u, v))

for u,v,a in G.edges(data=True):
    if not have_bidirectional_relationship(G, u, v) and a["t"] == "warp":
        oneway_connections.add((u, v))

#print (biconnections)
#print (len(biconnections))
G.remove_nodes_from(list(nx.isolates(G)))

# Add extra attributes
for v in map_bidir_edge_attributes:
    mpair = v[0]
    attrs = v[1]
    try:
        G.edges[mpair[0], mpair[1]].update(attrs)
    except:
        a = "a"
    try:
        G.edges[mpair[1], mpair[0]].update(attrs)
    except:
        a = "a"

def cut_graph_with_requirements(G, requires_has):
    G_out = G.copy()
    for u,v,a in G.edges(data=True):
        for block in a["requires"]:
            if block not in requires_has:
                try:
                    G_out.remove_edge(u,v)
                except:
                    a = "a"
                try:
                    G_out.remove_edge(v,u)
                except:
                    a = "a"
    return G_out

def cut_graph_warppairs(G, pairs):
    G_out = G.copy()
    for u,v,a in G.edges(data=True):
        if a["t"] != "warp":
            continue
        
        for p in pairs:
            if u in p or v in p:
                try:
                    G_out.remove_edge(u,v)
                except:
                    a = "a"
                try:
                    G_out.remove_edge(v,u)
                except:
                    a = "a"
    return G_out

def bind_graph_warppairs(G, pairs):
    G_out = G.copy()
    for p in pairs:
        if len(p[0]) > 1:
            w_from = p[1]
            w_to = p[0]
        else:
            w_from = p[0]
            w_to = p[1]
        
        if (len(w_from) == 2 and len(w_to) == 2):
            G_out.add_edge(w_from[0], w_to[0], t="warp", requires=[])
            G_out.add_edge(w_from[1], w_to[1], t="warp", requires=[])
            G_out.add_edge(w_to[0], w_from[0], t="warp", requires=[])
            G_out.add_edge(w_to[1], w_from[1], t="warp", requires=[])
            continue
        
        #if (len(w_from) != 1):
        #    print ("AAAAAAAAAAAAAAAA", p)

        for w_f in w_from:
            G_out.add_edge(w_f, w_to[0], t="warp", requires=[])

        for w in w_to:
            G_out.add_edge(w, w_from[0], t="warp", requires=[])
    return G_out

def try_path(G_mod, a, b):
    #return nx.has_path(G_mod, a, b)
    
    # TODO: verify pokecenter deathwarps for each step?

    try:
        return nx.has_path(G_mod, a, b)
    except:
        return False

def try_path_or_fail(G_mod, a, b):
    ret = try_path(G_mod, a, b)
    
    if not ret:
        raise Exception("Failed navigation from " + a + " to " + b)
    
    return ret

def verify_graph(G):
    try:
        requires_has = []
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_LITTLEROOT_TOWN", "MAP_ROUTE103")
        try_path_or_fail(G_mod, "MAP_ROUTE103", "MAP_LITTLEROOT_TOWN")
        try_path_or_fail(G_mod, "MAP_LITTLEROOT_TOWN", "MAP_PETALBURG_CITY_GYM_WARP0")

        #try:
        #    print (compound_check, nx.shortest_path(G_mod, "MAP_LITTLEROOT_TOWN", "MAP_PETALBURG_CITY_GYM_WARP0")
        #except:
        #    return False

        requires_has += ["wally"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_PETALBURG_CITY_GYM_WARP0", "MAP_RUSTBORO_CITY_GYM")
        try_path_or_fail(G_mod, "MAP_RUSTBORO_CITY_GYM", "MAP_RUSTBORO_CITY")

        # Player has gym1 and can now get savepeeko
        requires_has += ["gym1"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_RUSTBORO_CITY", "MAP_RUSTURF_TUNNEL_WARP0") # Meet panicked Devon guy on the way
        try_path_or_fail(G_mod, "MAP_RUSTURF_TUNNEL_WARP0", "MAP_RUSTBORO_CITY") # panicked Devon guy teleports us
        try_path_or_fail(G_mod, "MAP_RUSTBORO_CITY_DEVON_CORP_3F", "MAP_RUSTBORO_CITY") # Get pokenav stuff

        requires_has += ["savepeeko"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_RUSTBORO_CITY", "MAP_ROUTE104_MR_BRINEYS_HOUSE") # TODO: Maybe skip Briney as an explicit step?
        try_path_or_fail(G_mod, "MAP_ROUTE104_MR_BRINEYS_HOUSE", "MAP_DEWFORD_TOWN")
        try_path_or_fail(G_mod, "MAP_DEWFORD_TOWN", "MAP_GRANITE_CAVE_STEVENS_ROOM")

        #nx.shortest_path(G_mod, "MAP_ROUTE104_MR_BRINEYS_HOUSE", "MAP_GRANITE_CAVE_STEVENS_ROOM")

        requires_has += ["letter"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_GRANITE_CAVE_STEVENS_ROOM", "MAP_SLATEPORT_CITY")
        try_path_or_fail(G_mod, "MAP_SLATEPORT_CITY", "MAP_SLATEPORT_CITY_STERNS_SHIPYARD_1F")

        requires_has += ["sterngoods"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_SLATEPORT_CITY", "MAP_SLATEPORT_CITY_OCEANIC_MUSEUM_2F")

        requires_has += ["museum"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_SLATEPORT_CITY", "MAP_MAUVILLE_CITY")
        try_path_or_fail(G_mod, "MAP_MAUVILLE_CITY", "MAP_MAUVILLE_CITY_GYM")

        requires_has += ["gym3"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_MAUVILLE_CITY", "MAP_MAUVILLE_CITY_HOUSE1")
        requires_has += ["rocksmash"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_MAUVILLE_CITY", "MAP_FALLARBOR_TOWN")
        try_path_or_fail(G_mod, "MAP_FALLARBOR_TOWN", "MAP_ROUTE114")
        try_path_or_fail(G_mod, "MAP_FALLARBOR_TOWN", "MAP_METEOR_FALLS_1F_1R_WARP0")

        requires_has += ["meteorite"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_METEOR_FALLS_1F_1R_WARP0", "MAP_MT_CHIMNEY")
        try_path_or_fail(G_mod, "MAP_MT_CHIMNEY", "MAP_LAVARIDGE_TOWN")
        try_path_or_fail(G_mod, "MAP_LAVARIDGE_TOWN", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP25")
        try_path_or_fail(G_mod, "MAP_LAVARIDGE_TOWN_GYM_1F_WARP25", "MAP_LAVARIDGE_TOWN") # goggles

        requires_has += ["goggles"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_LAVARIDGE_TOWN", "MAP_RUSTURF_TUNNEL_WARP1") # strength from the tunnel guy

        #print (nx.shortest_path(G_mod, "MAP_LAVARIDGE_TOWN_GYM_1F", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP25"))

        requires_has += ["strength"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_RUSTURF_TUNNEL_WARP1", "MAP_DEWFORD_TOWN_GYM")

        requires_has += ["flash"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_DEWFORD_TOWN_GYM", "MAP_PETALBURG_CITY_GYM_WARP34")

        #print (nx.shortest_path(G_mod, "MAP_LITTLEROOT_TOWN", "MAP_PETALBURG_CITY_GYM_WARP34"))

        requires_has += ["surf"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_PETALBURG_CITY_WALLYS_HOUSE", "MAP_ROUTE118")
        #nx.shortest_path(G_mod, "MAP_PETALBURG_CITY_WALLYS_HOUSE", "MAP_ROUTE118")

        try_path_or_fail(G_mod, "MAP_PETALBURG_CITY_WALLYS_HOUSE", "MAP_ROUTE119_WEATHER_INSTITUTE_2F")

        requires_has += ["weatherinst"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_ROUTE119_WEATHER_INSTITUTE_2F", "MAP_FORTREE_CITY")
        try_path_or_fail(G_mod, "MAP_FORTREE_CITY", "MAP_ROUTE120")

        requires_has += ["scope"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_FORTREE_CITY", "MAP_FORTREE_CITY_GYM")

        requires_has += ["fly"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_FORTREE_CITY_GYM", "MAP_LILYCOVE_CITY")
        try_path_or_fail(G_mod, "MAP_LILYCOVE_CITY", "MAP_MT_PYRE_SUMMIT")

        requires_has += ["magmaemblem"]
        G_mod = cut_graph_with_requirements(G, requires_has)
        try_path_or_fail(G_mod, "MAP_MT_PYRE_SUMMIT", "MAP_MAGMA_HIDEOUT_4F")

        requires_has += ["magmadone"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_MAGMA_HIDEOUT_4F", "MAP_SLATEPORT_CITY")
        try_path_or_fail(G_mod, "MAP_SLATEPORT_CITY", "MAP_SLATEPORT_CITY_HARBOR")

        requires_has += ["aquasub"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_SLATEPORT_CITY", "MAP_AQUA_HIDEOUT_1F")
        try_path_or_fail(G_mod, "MAP_AQUA_HIDEOUT_1F", "MAP_AQUA_HIDEOUT_B2F_WARP8") # TODO be more specific

        requires_has += ["aquagone"]
        G_mod = cut_graph_with_requirements(G, requires_has)
        try_path_or_fail(G_mod, "MAP_AQUA_HIDEOUT_B2F_WARP8", "MAP_MOSSDEEP_CITY")
        try_path_or_fail(G_mod, "MAP_MOSSDEEP_CITY", "MAP_MOSSDEEP_CITY_GYM_WARP13") # TODO be more specific

        try_path_or_fail(G_mod, "MAP_MOSSDEEP_CITY_GYM", "MAP_MOSSDEEP_CITY_SPACE_CENTER_2F")
        try_path_or_fail(G_mod, "MAP_MOSSDEEP_CITY_SPACE_CENTER_2F", "MAP_MOSSDEEP_CITY_STEVENS_HOUSE")

        requires_has += ["dive"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        # TODO: verify player has surf + dive before room9, warps to MAP_ROUTE128
        try_path_or_fail(G_mod, "MAP_MOSSDEEP_CITY_STEVENS_HOUSE", "MAP_SEAFLOOR_CAVERN_ENTRANCE")
        try_path_or_fail(G_mod, "MAP_MOSSDEEP_CITY_STEVENS_HOUSE", "MAP_SEAFLOOR_CAVERN_ROOM9")
        try_path_or_fail(G_mod, "MAP_ROUTE128", "MAP_SOOTOPOLIS_CITY")
        try_path_or_fail(G_mod, "MAP_SOOTOPOLIS_CITY", "MAP_CAVE_OF_ORIGIN_B1F")

        requires_has += ["spicyweatherwallace"]
        G_mod = cut_graph_with_requirements(G, requires_has)
        try_path_or_fail(G_mod, "MAP_CAVE_OF_ORIGIN_B1F", "MAP_SKY_PILLAR_ENTRANCE")
        try_path_or_fail(G_mod, "MAP_SKY_PILLAR_ENTRANCE", "MAP_SKY_PILLAR_OUTSIDE")
        try_path_or_fail(G_mod, "MAP_SKY_PILLAR_OUTSIDE", "MAP_SKY_PILLAR_TOP")

        # Fly
        try_path_or_fail(G_mod, "MAP_SKY_PILLAR_TOP", "MAP_SOOTOPOLIS_CITY")

        requires_has += ["talkleaders"]
        G_mod = cut_graph_with_requirements(G, requires_has)
        try_path_or_fail(G_mod, "MAP_SOOTOPOLIS_CITY", "MAP_SOOTOPOLIS_CITY_GYM_1F")
        try_path_or_fail(G_mod, "MAP_SOOTOPOLIS_CITY_GYM_B1F", "MAP_SOOTOPOLIS_CITY_GYM_1F")

        requires_has += ["waterfall"]
        G_mod = cut_graph_with_requirements(G, requires_has)

        try_path_or_fail(G_mod, "MAP_SOOTOPOLIS_CITY", "MAP_EVER_GRANDE_CITY")

        try_path_or_fail(G_mod, "MAP_EVER_GRANDE_CITY", "MAP_EVER_GRANDE_CITY_POKEMON_LEAGUE_1F")
        try_path_or_fail(G_mod, "MAP_EVER_GRANDE_CITY_POKEMON_LEAGUE_1F", "MAP_EVER_GRANDE_CITY_SIDNEYS_ROOM")
        try_path_or_fail(G_mod, "MAP_EVER_GRANDE_CITY_SIDNEYS_ROOM", "MAP_EVER_GRANDE_CITY_PHOEBES_ROOM")
        try_path_or_fail(G_mod, "MAP_EVER_GRANDE_CITY_PHOEBES_ROOM", "MAP_EVER_GRANDE_CITY_GLACIAS_ROOM")
        try_path_or_fail(G_mod, "MAP_EVER_GRANDE_CITY_GLACIAS_ROOM", "MAP_EVER_GRANDE_CITY_DRAKES_ROOM")
        try_path_or_fail(G_mod, "MAP_EVER_GRANDE_CITY_DRAKES_ROOM", "MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM")
        try_path_or_fail(G_mod, "MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM", "MAP_EVER_GRANDE_CITY_HALL_OF_FAME")

        print (True)
        return True
    except Exception as e:
        print (e)
        return False
    #print (nx.shortest_path(G_mod, "MAP_LITTLEROOT_TOWN", "MAP_EVER_GRANDE_CITY_HALL_OF_FAME"))

a,b = [list(c) for c in zip(*biconnections)]
bidir_warps = a+b

bidir_warppairs = []

# We need to figure out pairs of warps that both go to the same warp
# (ie, indoors warps with two tiles, that map to one warp tile outside)
# TODO: also pair two-and-two warps, like the cable car station and Jagged Pass?
for v in biconnections:

    dontedit = False
    for m in map_donot_edit:
        if m in v[0] or m in v[1]:
            dontedit = True
    for w in mapwarp_donot_edit:
        if w == v[0] or w == v[1]:
            dontedit = True

    if dontedit:
        continue

    out1 = [v[0]]
    out2 = [v[1]]
    for v2 in oneway_connections:
        if v[0] in v2:
            out2 += [v2[0] if v2[0] != v[0] else v2[1]]
        if v[1] in v2:
            out1 += [v2[0] if v2[0] != v[1] else v2[1]]
    bidir_warppairs += [out1]
    bidir_warppairs += [out2]

'''
for v in bidir_warppairs:
    for v2 in v:
        if "PETALBURG" in v2:
            print (v)
            break
'''
bidir_warppairs = sorted(list(bidir_warppairs))

#for v in bidir_warppairs:
#    print (v)

print (len(bidir_warppairs))

def pop_random(lst, local_random):
    idx = local_random.randrange(0, len(lst))
    return lst.pop(idx)

def randompair_list(lst_orig, rand_idx):
    local_random = random.Random()
    local_random.seed(rand_idx)

    lst = lst_orig.copy()
    new_pairs = []
    no_infloops = 0
    while lst:
        rand1 = pop_random(lst, local_random)
        rand2 = pop_random(lst, local_random)
        
        if no_infloops > 50:
            pair = rand1, rand2
            new_pairs.append(pair)
            no_infloops = 0
            #print ("Forced pair:", rand1, rand2)
            continue
        
        cant_link = False

        for rand1_w in rand1:
            for rand2_w in rand2:
                # Don't link dead ends together
                if warpnode_getmap(rand1_w) in map_deadends and warpnode_getmap(rand2_w) in map_deadends:
                    cant_link = True
                
                # Some story events are stubborn.
                if warpnode_getmap(rand1_w) in map_require_multidoors and map_numdoors[warpnode_getmap(rand2_w)] < 4:
                    cant_link = True
                
                # Don't link maps with themselves
                if warpnode_getmap(rand1_w) == warpnode_getmap(rand2_w):
                    cant_link = True

        if cant_link:
            lst.append(rand1)
            lst.append(rand2)
            no_infloops += 1
            continue

        #if warpnode_getmap(rand1) == "MAP_RUSTBORO_CITY_GYM" or warpnode_getmap(rand2) == "MAP_RUSTBORO_CITY_GYM":
        #    print (rand1, rand2)
        
        pair = rand1, rand2
        new_pairs.append(pair)
        no_infloops = 0
    return new_pairs

def warpnode_getmap(w_id):
    if "_WARP" not in w_id:
        return -1
    return w_id.split("_WARP")[0]

def warpnode_getidx(w_id):
    if "_WARP" not in w_id:
        return -1
    return int(w_id.split("_WARP")[1])

def edit_map_warp(m_id, w_idx, map_to, map_to_w_idx):
    map_folder = os.path.join(mapdata_dir, map_id_to_folder[m_id])
    map_json = os.path.join(map_folder, "map.json")

    f = open(map_json, "r")
    data = json.load(f)
    f.close()
    
    data["warp_events"][w_idx]["dest_map"] = map_to
    data["warp_events"][w_idx]["dest_warp_id"] = map_to_w_idx
    
    f = open(map_json, "w")
    data = json.dump(data, f)
    f.close()

def apply_random_warppairs(pairs):
    for p in pairs:
        if len(p[0]) > 1:
            w_from = p[1]
            w_to = p[0]
        else:
            w_from = p[0]
            w_to = p[1]

        if (len(w_from) == 2 and len(w_to) == 2):
            edit_map_warp(warpnode_getmap(w_from[0]), warpnode_getidx(w_from[0]), warpnode_getmap(w_to[0]), warpnode_getidx(w_to[0]))
            edit_map_warp(warpnode_getmap(w_from[1]), warpnode_getidx(w_from[1]), warpnode_getmap(w_to[1]), warpnode_getidx(w_to[1]))
            edit_map_warp(warpnode_getmap(w_to[0]), warpnode_getidx(w_to[0]), warpnode_getmap(w_from[0]), warpnode_getidx(w_from[0]))
            edit_map_warp(warpnode_getmap(w_to[1]), warpnode_getidx(w_to[1]), warpnode_getmap(w_from[1]), warpnode_getidx(w_from[1]))
            continue
        
        if (len(w_from) != 1):
            print ("AAAAAAAAAAAAAAAA", p)

        for w_f in w_from:
            edit_map_warp(warpnode_getmap(w_f), warpnode_getidx(w_f), warpnode_getmap(w_to[0]), warpnode_getidx(w_to[0]))
        for w in w_to:
            edit_map_warp(warpnode_getmap(w), warpnode_getidx(w), warpnode_getmap(w_from[0]), warpnode_getidx(w_from[0]))

G_rand_cut = cut_graph_warppairs(G, bidir_warppairs)

def gen_graph_for_seed(G_rand_cut, rand_idx):
    rand_bidir_warppairs = randompair_list(bidir_warppairs, rand_idx)
    
    #print (rand_bidir_warppairs[0])
    #print (rand_bidir_warppairs[1])
    #print (rand_bidir_warppairs[2])
    
    G_rand = bind_graph_warppairs(G_rand_cut, rand_bidir_warppairs)
    
    return G_rand

def attempt_seed(G_rand_cut, rand_idx):
    global found_seed, num_threads
    #print (rand_idx)
    G_rand = gen_graph_for_seed(G_rand_cut, rand_idx)
    
    if (verify_graph(G_rand)):
        found_seed = rand_idx
        print ("Found seed!", rand_idx)
    
    #found_seed = rand_idx
    time.sleep(0.01)
    num_threads -= 1

print(verify_graph(G))

def find_random_seed_and_apply():
    global G, found_seed, threads, num_threads, rand_idx

    while True:
        if found_seed != -1:
            break
        if num_threads >= 50:
            time.sleep(0.01)
            continue

        print (rand_idx)
        x = threading.Thread(target=attempt_seed, args=(G_rand_cut.copy(), rand_idx,))
        num_threads += 1
        x.start()
        threads += [x]
        
        # Update list
        if len(threads) > 1000:
            for t in threads:
                t.handled = False
                if not t.is_alive():
                    t.handled = True
            threads = [t for t in threads if not t.handled]
        
        rand_idx += 1

    for t in threads:
        t.join()

    # Reseed and apply
    rand_bidir_warppairs = randompair_list(bidir_warppairs, found_seed)
    apply_random_warppairs(rand_bidir_warppairs)

    G_rand = gen_graph_for_seed(G_rand_cut, found_seed)
    G = G_rand

def print_routing():
    deps = ["wally"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_LITTLEROOT_TOWN", "MAP_RUSTBORO_CITY_GYM"))
    deps += ["gym1"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_RUSTBORO_CITY_GYM", "MAP_RUSTBORO_CITY"))
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_RUSTBORO_CITY", "MAP_RUSTURF_TUNNEL_WARP0"))
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_RUSTURF_TUNNEL_WARP0", "MAP_RUSTBORO_CITY"))
    deps += ["savepeeko"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_RUSTBORO_CITY_DEVON_CORP_3F", "MAP_RUSTBORO_CITY"))
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_RUSTBORO_CITY", "MAP_GRANITE_CAVE_STEVENS_ROOM"))
    deps += ["letter"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_GRANITE_CAVE_STEVENS_ROOM", "MAP_SLATEPORT_CITY_STERNS_SHIPYARD_1F"))
    deps += ["sterngoods"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_SLATEPORT_CITY_STERNS_SHIPYARD_1F", "MAP_SLATEPORT_CITY_OCEANIC_MUSEUM_2F"))
    deps += ["museum"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_SLATEPORT_CITY_OCEANIC_MUSEUM_2F", "MAP_MAUVILLE_CITY"))
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_MAUVILLE_CITY", "MAP_MAUVILLE_CITY_GYM"))
    deps += ["gym3"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_MAUVILLE_CITY_GYM", "MAP_MAUVILLE_CITY_HOUSE1"))
    deps += ["rocksmash"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_MAUVILLE_CITY_HOUSE1", "MAP_METEOR_FALLS_1F_1R_WARP0"))
    deps += ["meteorite"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_METEOR_FALLS_1F_1R_WARP0", "MAP_MT_CHIMNEY"))
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_MT_CHIMNEY", "MAP_LAVARIDGE_TOWN_GYM_1F_WARP25"))
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_LAVARIDGE_TOWN_GYM_1F_WARP25", "MAP_LAVARIDGE_TOWN"))
    deps += ["goggles"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_LAVARIDGE_TOWN", "MAP_RUSTURF_TUNNEL_WARP1"))
    deps += ["strength"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_RUSTURF_TUNNEL_WARP1", "MAP_DEWFORD_TOWN_GYM"))
    deps += ["flash"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_DEWFORD_TOWN_GYM", "MAP_PETALBURG_CITY_GYM_WARP34"))
    deps += ["surf"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_PETALBURG_CITY_WALLYS_HOUSE", "MAP_ROUTE119_WEATHER_INSTITUTE_2F"))
    deps += ["weatherinst"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_ROUTE119_WEATHER_INSTITUTE_2F", "MAP_ROUTE120"))
    deps += ["scope"]
    print(nx.shortest_path(cut_graph_with_requirements(G, deps), "MAP_ROUTE120", "MAP_FORTREE_CITY_GYM"))
    deps += ["fly"]


find_random_seed_and_apply()
print_routing()

draw_network = False
if draw_network:
    # explicitly set positions
    pos = nx.spring_layout(G, scale=1000)

    options = {
        "font_size": 6,
        "node_size": 300,
        "node_color": "white",
        "edgecolors": "black",
        "linewidths": 2,
        "width": 2,
    }
    nx.draw_networkx(G, pos, **options)

    # Set margins for the axes so that nodes aren't clipped
    ax = plt.gca()
    #ax.margins(0.20)
    plt.axis("off")
    plt.show()
