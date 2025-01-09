from typing import TYPE_CHECKING

from BaseClasses import ItemClassification as IC
from Fill import FillError

from ..Items import ITEM_TABLE, item_factory
from ..Options import DungeonItem
from .Dungeons import get_dungeon_item_pool_player

if TYPE_CHECKING:
    from .. import TWWWorld

import random

VANILLA_DUNGEON_ITEM_LOCATIONS: dict[str, list[str]] = {
    "DRC Small Key": [
        "Dragon Roost Cavern - First Room",
        "Dragon Roost Cavern - Boarded Up Chest",
        "Dragon Roost Cavern - Rat Room Boarded Up Chest",
        "Dragon Roost Cavern - Bird's Nest",
    ],
    "FW Small Key": [
        "Forbidden Woods - Vine Maze Right Chest"
    ],
    "TotG Small Key": [
        "Tower of the Gods - Hop Across Floating Boxes",
        "Tower of the Gods - Floating Platforms Room"
    ],
    "ET Small Key": [
        "Earth Temple - Transparent Chest in First Crypt",
        "Earth Temple - Casket in Second Crypt",
        "Earth Temple - End of Foggy Room With Floormasters",
    ],
    "WT Small Key": [
        "Wind Temple - Spike Wall Room - First Chest",
        "Wind Temple - Chest Behind Seven Armos"
    ],

    "DRC Big Key":  ["Dragon Roost Cavern - Big Key Chest"],
    "FW Big Key":   ["Forbidden Woods - Big Key Chest"],
    "TotG Big Key": ["Tower of the Gods - Big Key Chest"],
    "ET Big Key":   ["Earth Temple - Big Key Chest"],
    "WT Big Key":   ["Wind Temple - Big Key Chest"],

    "DRC Dungeon Map":  ["Dragon Roost Cavern - Alcove With Water Jugs"],
    "FW Dungeon Map":   ["Forbidden Woods - First Room"],
    "TotG Dungeon Map": ["Tower of the Gods - Chest Behind Bombable Walls"],
    "FF Dungeon Map":   ["Forsaken Fortress - Chest Outside Upper Jail Cell"],
    "ET Dungeon Map":   ["Earth Temple - Transparent Chest In Warp Pot Room"],
    "WT Dungeon Map":   ["Wind Temple - Chest In Many Cyclones Room"],

    "DRC Compass":  ["Dragon Roost Cavern - Rat Room"],
    "FW Compass":   ["Forbidden Woods - Vine Maze Left Chest"],
    "TotG Compass": ["Tower of the Gods - Skulls Room Chest"],
    "FF Compass":   ["Forsaken Fortress - Chest Guarded By Bokoblin"],
    "ET Compass":   ["Earth Temple - Chest In Three Blocks Room"],
    "WT Compass":   ["Wind Temple - Chest In Middle Of Hub Room"],
}


def generate_itempool(world: "TWWWorld") -> None:
    """
    Generate the item pool for the world.

    :param world: The Wind Waker game world.
    """
    multiworld = world.multiworld

    # Get the core pool of items.
    pool, precollected_items = get_pool_core(world)

    # Add precollected items to the multiworld's `precollected_items` list.
    for item in precollected_items:
        multiworld.push_precollected(item_factory(item, world))

    # Place a "Victory" item on "Defeat Ganondorf" for the spoiler log.
    world.get_location("Defeat Ganondorf").place_locked_item(item_factory("Victory", world))

    # Create the pool of the remaining shuffled items.
    items = item_factory(pool, world)
    multiworld.random.shuffle(items)

    multiworld.itempool += items

    # Dungeon items should already be created, so handle those separately.
    handle_dungeon_items(world)


def get_pool_core(world: "TWWWorld") -> tuple[list[str], list[str]]:
    """
    Get the core pool of items and precollected items for the world.

    :param world: The Wind Waker game world.
    :return: A tuple of the item pool and precollected items.
    """
    pool: list[str] = []
    precollected_items: list[str] = []

    # Split items into three different pools: progression, useful, and filler.
    progression_pool: list[str] = []
    useful_pool: list[str] = []
    filler_pool: list[str] = []
    for item, data in ITEM_TABLE.items():
        if data.type == "Item":
            adjusted_classification = world.determine_item_classification(item)
            classification = data.classification if adjusted_classification is None else adjusted_classification

            if classification & IC.progression:
                progression_pool.extend([item] * data.quantity)
            elif classification & IC.useful:
                useful_pool.extend([item] * data.quantity)
            else:
                filler_pool.extend([item] * data.quantity)

    # The number of items in the item pool should be the same as the number of locations in the world.
    num_items_left_to_place = len(world.multiworld.get_locations(world.player)) - 1

    # Account for the dungeon items that have already been created.
    for dungeon in world.dungeons.values():
        num_items_left_to_place -= len(dungeon.all_items)

    # All progression items are added to the item pool.
    if len(progression_pool) > num_items_left_to_place:
        raise FillError(
            "There are insufficient locations to place progression items! "
            f"Trying to place {len(progression_pool)} items in only {num_items_left_to_place} locations."
        )
    pool.extend(progression_pool)
    num_items_left_to_place -= len(progression_pool)

    # Assign the remaining items to item pools in the world.
    world.multiworld.random.shuffle(useful_pool)
    world.multiworld.random.shuffle(filler_pool)
    world.useful_pool = useful_pool
    world.filler_pool = filler_pool

    # If the player starts with a sword, add one to the precollected items list and remove one from the item pool.
    if world.options.sword_mode == "start_with_sword":
        precollected_items.append("Progressive Sword")
        num_items_left_to_place += 1
        pool.remove("Progressive Sword")
    # Or, if it's swordless mode, remove all swords from the item pool.
    elif world.options.sword_mode == "swordless":
        while "Progressive Sword" in pool:
            num_items_left_to_place += 1
            pool.remove("Progressive Sword")


    if world.options.better_filler != "standard_filler":
        better_filler_items = ["Blue Chu Jelly",
                              "Skull Necklace",
                              "Boko Baba Seed",
                              "Golden Feather",
                              "Knight's Crest",
                              "Red Chu Jelly",
                              "Green Chu Jelly",
                              "Joy Pendant",
                              "All-Purpose Bait",
                              "Hyoi Pear",
                              "Green Rupee",
                              "Blue Rupee",
                              "Yellow Rupee",
                              "Red Rupee",
                              "Purple Rupee",
                              "10 Arrows (Pickup)",
                              "5 Bombs (Pickup)",
                              "Small Magic Jar (Pickup)",
                              "Large Magic Jar (Pickup)",
                              "Heart (Pickup)",
                              "Three Hearts (Pickup)",]
        
        better_filler_count = 0

        if not world.options.progression_treasure_charts and (world.options.better_filler == "remove_treasure_charts" or world.options.better_filler == "remove_both_charts"):
            filler_pool.remove("Treasure Chart 1")
            filler_pool.remove("Treasure Chart 2")
            filler_pool.remove("Treasure Chart 3")
            filler_pool.remove("Treasure Chart 4")
            filler_pool.remove("Treasure Chart 5")
            filler_pool.remove("Treasure Chart 6")
            filler_pool.remove("Treasure Chart 7")
            filler_pool.remove("Treasure Chart 8")
            filler_pool.remove("Treasure Chart 9")
            filler_pool.remove("Treasure Chart 10")
            filler_pool.remove("Treasure Chart 11")
            filler_pool.remove("Treasure Chart 12")
            filler_pool.remove("Treasure Chart 13")
            filler_pool.remove("Treasure Chart 14")
            filler_pool.remove("Treasure Chart 15")
            filler_pool.remove("Treasure Chart 16")
            filler_pool.remove("Treasure Chart 17")
            filler_pool.remove("Treasure Chart 18")
            filler_pool.remove("Treasure Chart 19")
            filler_pool.remove("Treasure Chart 20")
            filler_pool.remove("Treasure Chart 21")
            filler_pool.remove("Treasure Chart 22")
            filler_pool.remove("Treasure Chart 23")
            filler_pool.remove("Treasure Chart 24")
            filler_pool.remove("Treasure Chart 25")
            filler_pool.remove("Treasure Chart 26")
            filler_pool.remove("Treasure Chart 27")
            filler_pool.remove("Treasure Chart 28")
            filler_pool.remove("Treasure Chart 29")
            filler_pool.remove("Treasure Chart 30")
            filler_pool.remove("Treasure Chart 31")
            filler_pool.remove("Treasure Chart 32")
            filler_pool.remove("Treasure Chart 33")
            filler_pool.remove("Treasure Chart 34")
            filler_pool.remove("Treasure Chart 35")
            filler_pool.remove("Treasure Chart 36")
            filler_pool.remove("Treasure Chart 37")
            filler_pool.remove("Treasure Chart 38")
            filler_pool.remove("Treasure Chart 39")
            filler_pool.remove("Treasure Chart 40")
            filler_pool.remove("Treasure Chart 41")

            better_filler_count += 41

        if not world.options.progression_triforce_charts and (world.options.better_filler == "remove_triforce_charts" or world.options.better_filler == "remove_both_charts"):
            filler_pool.remove("Triforce Chart 1")
            filler_pool.remove("Triforce Chart 2")
            filler_pool.remove("Triforce Chart 3")
            filler_pool.remove("Triforce Chart 4")
            filler_pool.remove("Triforce Chart 5")
            filler_pool.remove("Triforce Chart 6")
            filler_pool.remove("Triforce Chart 7")
            filler_pool.remove("Triforce Chart 8")

            better_filler_count += 8

        better_filler_list = random.choices(better_filler_items,k=better_filler_count)
        for item in better_filler_list:
            filler_pool.append(item)

    # Place useful items, then filler items to fill out the remaining locations.
    pool.extend([world.get_filler_item_name() for _ in range(num_items_left_to_place)])

    return pool, precollected_items


def handle_dungeon_items(world: "TWWWorld") -> None:
    """
    Handle the placement of dungeon items in the world.

    :param world: The Wind Waker game world.
    """
    player = world.player
    multiworld = world.multiworld
    options = world.options

    dungeon_items = [
        item
        for item in get_dungeon_item_pool_player(world)
        if item.name not in multiworld.worlds[player].dungeon_local_item_names
    ]

    for x in range(len(dungeon_items) - 1, -1, -1):
        item = dungeon_items[x]

        # Consider dungeon items in non-required dungeons as filler.
        if item.dungeon.name in world.boss_reqs.banned_dungeons:
            item.classification = IC.filler

        option: DungeonItem
        if item.type == "Big Key":
            option = options.randomize_bigkeys
        elif item.type == "Small Key":
            option = options.randomize_smallkeys
        else:
            option = options.randomize_mapcompass

        if option == "startwith":
            dungeon_items.pop(x)
            multiworld.push_precollected(item)
            multiworld.itempool.append(item_factory(world.get_filler_item_name(), world))
        elif option == "vanilla":
            for location_name in VANILLA_DUNGEON_ITEM_LOCATIONS[item.name]:
                location = world.get_location(location_name)
                if location.item is None:
                    dungeon_items.pop(x)
                    location.place_locked_item(item)
                    break
            else:
                raise FillError(f"Could not place dungeon item in vanilla location: {item}")

    multiworld.itempool.extend([item for item in dungeon_items])
