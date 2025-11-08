import time
import random
import sys

# Print functions - slow for narrative, fast for UI
def slow_print(text, delay=0.03):
    # slow print for atmospheric narrative text
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def fast_print(text, delay=0.015):
    """Faster print for repeated deaths"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def quick_print(text):
    # Quick print for UI elements and menus
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.005)
    print()

# Room class
class Room:
    def __init__(self, name, description, items=None, neighbors=None, objects=None):
        self.name = name
        self.description = description
        self.items = items if items else []
        self.neighbors = neighbors if neighbors else {}
        self.objects = objects if objects else {}

    def describe(self):
        slow_print(f"\nYou are in the {self.name}.")
        slow_print(self.description)

# Game state
class GameState:
    def __init__(self, start_room):
        self.current_room = start_room
        self.inventory = []
        self.lives = 3
        self.max_lives = 5
        self.sanity = 100
        self.crucifix_protect = False
        self.survived_rooms = set()
        self.survived_count = 0
        self.game_over = False
        self.used_life_bonus = set()
        self.room_visited = set()
        self.room_death_count = {}
        self.turn_count = 0
        self.sanity_warnings = 0
        self.notes_read = set()
        self.escaped = False
        self.boss_defeated = False
        self.locked_box_opened = False

    def show_health(self):
        # Display health as hearts
        hearts = "♥ " * self.lives + "♡ " * (self.max_lives - self.lives)
        quick_print(f"Health: [{hearts}] ({self.lives}/{self.max_lives})")

    def show_sanity(self):
        # Display sanity as progress bar
        filled = int(self.sanity / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        quick_print(f"Sanity: [{bar}] ({self.sanity}/100)")

    def show_stats(self):
        # Display all stats quickly
        self.show_health()
        self.show_sanity()
        quick_print(f"Rooms explored: {self.survived_count}")

    def update_room_visit(self):
        # Track room visits
        if self.current_room.name not in self.survived_rooms:
            self.survived_rooms.add(self.current_room.name)
            self.survived_count = len(self.survived_rooms)
        self.room_visited.add(self.current_room.name)

    def lose_sanity(self, amount=5, cause=None):
        # Decrease sanity with atmospheric feedback
        self.sanity -= amount
        if cause:
            slow_print(cause)
        
        if self.sanity <= 0:
            slow_print("\nThe whispers are too loud now. They're all you can hear.")
            slow_print("Your thoughts aren't your own anymore. The house has you.")
            slow_print("You collapse, and the darkness welcomes you home.")
            self.game_over = True
            return True
        elif self.sanity <= 20 and self.sanity_warnings < 3:
            slow_print(f"Your hands are shaking. Everything feels wrong.")
            self.show_sanity()
            self.sanity_warnings += 1
        elif self.sanity <= 40:
            slow_print(f"The walls seem closer than before...")
            self.show_sanity()
        
        return False

    def gain_sanity(self, amount=10):
        # Increase sanity
        old_sanity = self.sanity
        self.sanity = min(100, self.sanity + amount)
        gained = self.sanity - old_sanity
        if gained > 0:
            slow_print(f"You take a breath. The fog in your head clears a little.")
            self.show_sanity()

    def passive_sanity_drain(self):
        # Gradual sanity loss over time
        self.turn_count += 1
        if self.turn_count % 5 == 0:
            self.sanity -= 2
            if self.sanity <= 0:
                slow_print("\nToo long. You've been here too long.")
                slow_print("The house has gotten inside your head.")
                self.game_over = True
                return True
        return False

    def lose_life(self, amount=1, cause=None):
        # Decrease health with consequences
        room_name = self.current_room.name
        self.room_death_count[room_name] = self.room_death_count.get(room_name, 0) + 1
        printer = fast_print if self.room_death_count[room_name] > 1 else slow_print

        if self.crucifix_protect:
            slow_print("The crucifix grows warm in your pocket. Something backs away.")
            slow_print("Whatever was reaching for you... it can't touch you. Not yet.")
            self.crucifix_protect = False
            self.gain_sanity(15)
            return False

        self.lives -= amount
        self.lose_sanity(15)
        
        if cause:
            printer(cause)
        self.show_health()
        
        if self.lives <= 0:
            slow_print("\nYour vision blurs. The floor rushes up to meet you.")
            slow_print("The last thing you hear is laughter. Or maybe crying.")
            slow_print("You can't tell anymore.")
            self.game_over = True
            return True
        return False

    def gain_life(self, amount=1):
        # Increase health
        rn = self.current_room.name
        if rn in self.used_life_bonus:
            slow_print("You try again, but there's nothing left here for you.")
            slow_print("The well has run dry.")
            return
        self.used_life_bonus.add(rn)
        self.lives = min(self.max_lives, self.lives + amount)
        self.gain_sanity(10)
        slow_print(f"Something shifts. You feel stronger.")
        self.show_health()

    def add_item(self, item):
        # Add item to inventory
        if item not in self.inventory:
            self.inventory.append(item)
            slow_print(f"You take the {item}.")
            self.gain_sanity(5)
            if item == "crucifix":
                self.crucifix_protect = True
                slow_print("The crucifix feels warm. Protective. Like it's watching over you.")
        else:
            slow_print(f"You already have the {item}.")

    def remove_item(self, item):
        # Remove item from inventory
        if item in self.inventory:
            self.inventory.remove(item)
            slow_print(f"The {item} is gone.")

    def show_map(self):
        # Display the estate map quickly
        def mark(name): 
            return "■" if name in self.room_visited else "□"
        
        print("\n" + "="*75)
        print("                    CRAMPTON ESTATE - FLOOR PLAN")
        print("="*75)
        print()
        print("                          ┏━━━━━━━━━━━━━┓")
        print("                          ┃    ATTIC    ┃")
        print(f"                          ┃      {mark('Attic')}      ┃")
        print("                          ┗━━━━━━┬━━━━━━┛")
        print("                                 │")
        print("    ┏━━━━━━━━━━┓   ┏━━━━━━━━━━━━┻━━━━━━━━━━━┓   ┏━━━━━━━━━━┓")
        print("    ┃KIDS BEDRM┃───┃   SECOND FLOOR HALL    ┃───┃MASTER BED┃")
        print(f"    ┃    {mark('Kids Bedroom')}   ┃   ┃          {mark('Second Floor Hall')}         ┃   ┃    {mark('Master Bedroom')}   ┃")
        print("    ┗━━━━━━━━━━┛   ┗━━━━━━━━━┬━━━━━━━━━━━━━┛   ┗━━━━┬━━━━━┛")
        print("                              │                        │")
        print("                      ┏━━━━━━━┴━━━━━━┓          ┏━━━━┻━━━━┓")
        print("                      ┃   BATHROOM   ┃          ┃ UTILITY ┃")
        print(f"                      ┃      {mark('Bathroom')}      ┃          ┃    {mark('Utility Room')}   ┃")
        print("                      ┗━━━━━━━━━━━━━━┛          ┗━━━━━━━━━┛")
        print("                              │")
        print("            ┏━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┓")
        print("            ┃         GRAND HALL                ┃")
        print(f"            ┃              {mark('Grand Hall')}                   ┃")
        print("            ┗━━┬━━━━━━━━━━━━━┬━━━━━━━━━━━━┬━━━━┛")
        print("               │             │            │")
        print("      ┏━━━━━━━━┴━━━━━━┓   ┏━━┴━━━━┓  ┏━━━┴━━━━━━┓")
        print("      ┃   LIBRARY     ┃   ┃DINING ┃  ┃  LIVING   ┃")
        print(f"      ┃      {mark('Library')}      ┃   ┃ ROOM ┃  ┃   ROOM   ┃")
        print(f"      ┗━━━━━━━┬━━━━━━┛   ┗━━━┬━━━┛  ┗━━━━━━━━━━┛")
        print("              │               │")
        print("      ┏━━━━━━━┴━━━━━━┓   ┏━━━┴━━━━━━┓")
        print("      ┃   BASEMENT   ┃   ┃  KITCHEN  ┃")
        print(f"      ┃      {mark('Basement')}      ┃   ┃     {mark('Kitchen')}    ┃")
        print("      ┗━━━━━━━━━━━━━━┛   ┗━━━━┬━━━━━━┛")
        print("                               │")
        print("                       ┏━━━━━━━┴━━━━━━━┓")
        print("                       ┃ CONSERVATORY  ┃")
        print(f"                       ┃      {mark('Conservatory')}       ┃")
        print("                       ┗━━━━━━━━━━━━━━━┛")
        print()
        print("Legend: ■ = visited  □ = unvisited")
        print("="*75 + "\n")

def read_note(game, note_id, note_text):
    # Read a note with slow printing for atmosphere
    if note_id in game.notes_read:
        slow_print("You've already read this. The words are the same.")
        return
    
    game.notes_read.add(note_id)
    slow_print("\n" + "-"*60)
    for line in note_text:
        slow_print(line)
    slow_print("-"*60 + "\n")
    game.gain_sanity(5)

# Item interaction functions
def examine_object(game, obj_name):
    # Examine an object in the room - handles items, health effects, and special actions
    obj_info = game.current_room.objects.get(obj_name)
    if not obj_info:
        slow_print(f"There's no {obj_name} here to examine.")
        return
    
    slow_print(obj_info["description"])
    
    # Handle health effects
    if "health" in obj_info:
        game.lives = max(0, min(game.max_lives, game.lives + obj_info["health"]))
        if obj_info["health"] < 0:
            slow_print("You feel pain shoot through you!")
        game.show_health()
        if game.lives <= 0:
            game.game_over = True
            return
    
    # Handle items
    if obj_info.get("items"):
        for item in obj_info["items"]:
            if item:
                game.add_item(item)
        obj_info["items"] = []
        # Update description if needed
        if "examined_description" in obj_info:
            obj_info["description"] = obj_info["examined_description"]

def search_cupboard(game):
    # Random encounter when searching kitchen cupboard
    outcomes = [
        ("Something scurries out and bites your ankle!", lambda: game.lose_life(1, "The bite burns. Infection sets in.")),
        ("Hands. Cold, dead hands reach out.", lambda: game.lose_life(1, "They're so cold. They pull you closer.")),
        ("A rusted blade falls out, cutting you.", lambda: game.lose_life(1, "Blood drips onto the floor.")),
        ("The door slams near your face.", lambda: game.lose_sanity(8, "That was too close.")),
        ("A small, rusted key hidden behind a false panel!", lambda: game.add_item("rusty key")),
        ("Nothing. Just cobwebs and rot.", lambda: game.lose_sanity(3, "The emptiness feels deliberate.")),
    ]
    outcome = random.choice(outcomes)
    slow_print(outcome[0])
    if callable(outcome[1]): 
        outcome[1]()

def search_wardrobe(game):
    # Random encounter when searching master bedroom wardrobe
    outcomes = [
        ("Something inside grabs you!", lambda: game.lose_life(1, "The wardrobe tries to swallow you.")),
        ("The door slams with a deafening bang.", lambda: game.lose_sanity(7, "Did something hear that?")),
        ("A wooden crucifix hangs inside, glowing faintly.", lambda: game.add_item("crucifix")),
        ("Empty. But you swear something moved.", lambda: game.lose_sanity(5, "The shadows weren't right."))
    ]
    outcome = random.choice(outcomes)
    slow_print(outcome[0])
    if callable(outcome[1]): 
        outcome[1]()

def use_cassette_player(game):
    # Play cassette tape in library for important clues
    if game.current_room.name != "Library":
        slow_print("There's nothing to play it on here.")
        game.lose_sanity(3)
        return
    
    if "cassette tape" not in game.inventory:
        slow_print("The cassette player is dusty but functional.")
        slow_print("There's no tape inside. You'll need to find one.")
        game.lose_sanity(2)
        return
    
    if "tape_played" in game.notes_read:
        slow_print("You've already played the tape. Once was enough.")
        return
    
    game.notes_read.add("tape_played")
    slow_print("You insert the cassette tape...")
    slow_print("Static crackles. Then a distorted voice:")
    time.sleep(1)
    slow_print('"Graeme... if you find this..."')
    time.sleep(1)
    slow_print('"Three things you need. The holy symbol protects..."')
    time.sleep(1)
    slow_print('"The blade strikes true... The book binds evil..."')
    time.sleep(1)
    slow_print('"Together... only together can you end this..."')
    time.sleep(1)
    slow_print('"The basement... that\'s where it sleeps..."')
    time.sleep(1)
    slow_print('"But the attic... secrets in the locked box... the crowbar..."')
    slow_print("")
    slow_print("The tape ends with a scream.")
    game.gain_sanity(20)

def use_crowbar_on_box(game):
    # Use crowbar to open locked box in attic
    if game.locked_box_opened:
        slow_print("The box is already open. Nothing remains inside.")
        return
    
    if "crowbar" not in game.inventory:
        slow_print("The box is sealed tight. You need something to pry it open.")
        game.lose_sanity(5, "The frustration gnaws at you.")
        return
    
    slow_print("You wedge the crowbar under the lid.")
    slow_print("Wood splinters. Metal groans. The lock breaks.")
    time.sleep(1)
    slow_print("Inside, you find a faded journal and a photograph.")
    time.sleep(1)
    game.locked_box_opened = True
    
    read_note(game, "locked_box_journal", [
        "Graeme's Final Journal Entry:",
        "",
        "October 31st, 1952",
        "",
        "Margaret is dead. Thomas too. Sarah vanished three days ago.",
        "I know what waits for me in the basement.",
        "",
        "If anyone finds this - you need three things:",
        "1. The CRUCIFIX from the master bedroom - it wards off evil",
        "2. The KNIFE from the kitchen - blessed steel cuts through darkness",
        "3. The ANCIENT BOOK from the library - contains the binding ritual",
        "",
        "Without all three, you cannot defeat what lurks below.",
        "The basement door requires the RUSTY KEY from the kitchen.",
        "",
        "The garden is death. Don't go outside.",
        "The mirrors show truth. Don't look at them.",
        "",
        "I'm going down now. I won't be coming back up.",
        "May God have mercy on whoever comes next.",
        "",
        "- Graeme Crampton"
    ])
    
    game.add_item("old photograph")
    slow_print("\nThe photograph shows a family: a man, woman, and two children.")
    slow_print("On the back is written: 'The Cramptons - Summer 1952'")
    slow_print("'Before everything went wrong.'")

def boss_fight(game):
    # Final confrontation in the basement - outcome depends on items collected
    slow_print("\n" + "="*75)
    slow_print("You unlock the basement door and descend into absolute darkness.")
    slow_print("The door slams shut behind you. A lock clicks.")
    slow_print("")
    time.sleep(1)
    slow_print("Something moves in the darkness. Multiple somethings.")
    slow_print("Red eyes open. One pair. Then another. Then dozens.")
    slow_print("")
    time.sleep(1)
    slow_print("A DARK FIGURE emerges from the shadows - tall, wrong, impossible.")
    slow_print("Its eyes burn like coals. It reaches for you with too many arms.")
    slow_print("This is the thing that killed the Cramptons.")
    slow_print("="*75)
    time.sleep(1)
    
    has_knife = "knife" in game.inventory
    has_crucifix = "crucifix" in game.inventory
    has_ancient_book = "ancient book" in game.inventory
    
    # Perfect victory - all three items
    if has_knife and has_crucifix and has_ancient_book:
        slow_print("\nYou hold the knife, crucifix, and ancient book.")
        slow_print("The book falls open to a page marked in dried blood.")
        slow_print("You begin reading the Latin words aloud...")
        time.sleep(1)
        slow_print("The crucifix blazes with holy light!")
        slow_print("The figure SCREAMS - a sound that shouldn't exist.")
        slow_print("You drive the knife forward with the last word of the ritual.")
        time.sleep(1)
        slow_print("The blade strikes true. The figure explodes into shadow and ash.")
        slow_print("The darkness lifts. The house... breathes out.")
        slow_print("The curse is broken. The Cramptons can finally rest.")
        game.boss_defeated = True
        game.escaped = True
        return True
    
    # Partial victory - knife and crucifix (no book for ritual)
    elif has_knife and has_crucifix:
        slow_print("\nYou hold the knife and crucifix together.")
        slow_print("The crucifix glows, weakening the figure.")
        slow_print("But without the book, you can't complete the ritual!")
        slow_print("You strike with the knife anyway!")
        time.sleep(1)
        slow_print("The figure staggers but fights back viciously!")
        game.lose_life(2, "Its claws rake across you!")
        if game.lives > 0:
            slow_print("With desperate fury, you drive it back into the shadows!")
            slow_print("It's not destroyed... but it's wounded. Banished. For now.")
            game.boss_defeated = True
            game.escaped = True
            return True
        return False
    
    # Crucifix only - can defend but not attack
    elif has_crucifix:
        slow_print("\nYou raise the crucifix desperately.")
        slow_print("It glows and pushes the figure back.")
        slow_print("But you have no weapon to finish it!")
        slow_print("The figure circles you, probing your defenses...")
        game.lose_life(3, "It finds a weakness and strikes!")
        if game.lives > 0:
            slow_print("You barely escape back up the stairs!")
            slow_print("You're not ready. You need more.")
            return False
        return False
    
    # Knife only - can attack but no protection
    elif has_knife:
        slow_print("\nYou grip the knife and charge!")
        slow_print("You stab the figure, but it barely notices.")
        slow_print("Without the crucifix's protection, you're vulnerable!")
        game.lose_life(4, "It grabs you with impossible strength!")
        return False
    
    # No items - instant death
    else:
        slow_print("\nYou have no weapons. No protection. No ritual.")
        slow_print("The figure is upon you instantly.")
        slow_print("You never stood a chance.")
        game.lives = 0
        slow_print("You have been consumed by the darkness.")
        return False

# Create all rooms with enhanced details and lore

grand_hall = Room(
    "Grand Hall",
    "The grand hall stretches before you, swallowed by darkness. A chandelier hangs overhead, swaying gently though there's no breeze. The air is thick and stale. Doors lead in all directions.",
    [],
    {},
    {
        "chandelier": {
            "description": "The crystals reflect faces that aren't there. Dozens of them. All watching you with hollow eyes.",
            "items": []
        },
        "paintings": {
            "description": "The eyes in every portrait follow you as you move. The Crampton family stares with expressions of terror and despair.",
            "items": []
        },
        "entrance note": {
            "description": "A note pinned to the wall, dated October 31st, 1952. The paper is yellowed and brittle.",
            "items": []
        }
    }
)

# Note added via examine
grand_hall.objects["entrance note"]["description"] = """A note in shaky handwriting:

'To whoever enters this house - turn back now.

If you cannot leave, then listen:
- The KITCHEN holds supplies and a key
- The LIBRARY contains knowledge 
- The ATTIC has secrets in a locked box
- The BASEMENT is where everything ends

Find what you need. Escape if you can.
But don't trust the mirrors. And never go to the garden.

- Margaret Crampton, Final Warning'"""

kitchen = Room(
    "Kitchen",
    "The smell hits you - rot and decay and something worse underneath. The kitchen hasn't been used in decades, but something's been here recently. Pots hang from hooks. A cupboard stands against the wall.",
    [],
    {},
    {
        "sink": {
            "description": "Dark liquid oozes from the drain, thick and viscous. It smells like old blood. The drain gurgles, almost laughing at you.",
            "items": []
        },
        "cupboard": {
            "description": "A wooden cupboard that might contain something useful... or something that will hurt you. Do you dare search it?",
            "items": [],
            "action": "search_cupboard"
        },
        "drawer": {
            "description": "A messy drawer full of old utensils. Among the cutlery, you spot a small knife with strange markings on the blade.",
            "items": ["knife"],
            "examined_description": "The drawer is empty now, just rusty spoons and forks remain."
        },
        "recipe note": {
            "description": """A recipe card with writing on the back:

'Day 4 in this hell

The scratching in the walls won't stop. Sarah says she hears 
children laughing upstairs, but there are no children here.
There haven't been children here for ten years.

Graeme says the basement key is hidden in the kitchen.
Behind a false panel in the cupboard.
He won't tell us why he locked the basement in the first place.

The RUSTY KEY - that's our way to answers. Or our doom.

I'm so scared. - Margaret'""",
            "items": []
        }
    }
)

library = Room(
    "Library",
    "Books line the walls from floor to ceiling, their spines cracked and faded. The darkness between shelves seems deeper than it should be. An old cassette player sits on a mahogany desk, covered in dust.",
    [],
    {},
    {
        "shelves": {
            "description": "You look away for just a second. When you look back, the books have rearranged themselves. Titles you didn't see before now face outward.",
            "items": []
        },
        "desk": {
            "description": "Papers are scattered across the desk, covered in frantic writing. The same phrase over and over: 'It watches from the attic. It knows. It knows. IT KNOWS.'",
            "items": []
        },
        "ancient book": {
            "description": "A leather-bound tome with strange symbols burned into the cover. It radiates cold. Inside are Latin texts and diagrams - an exorcism ritual. The ANCIENT BOOK OF BINDING.",
            "items": ["ancient book"],
            "examined_description": "The book's empty space on the shelf seems to pulse with darkness."
        },
        "cassette player": {
            "description": "An old cassette player from the 1950s. Surprisingly, it looks functional. There's a slot for a tape.",
            "items": [],
            "action": "use_cassette_player"
        },
        "journal": {
            "description": """A leather journal, water-damaged:

'October 28th, 1952 - Graeme Crampton

I found something in the basement. Something that shouldn't exist.
It killed Thomas. Just... took him. Sarah saw it happen and now 
she won't stop screaming.

I've locked the basement. The RUSTY KEY is hidden in the kitchen
cupboard, behind the false panel. No one can go down there.

But I know I'll have to eventually. To end this.

I'm gathering what I need:
- The CRUCIFIX from our bedroom - blessed by Father Michael
- The KNIFE from the kitchen - forged with iron from a church bell  
- The ANCIENT BOOK from this library - contains the binding ritual

If I fail... may God forgive me.'""",
            "items": []
        }
    }
)

basement = Room(
    "Basement",
    "The darkness here is absolute. It presses against you like a physical weight. The air tastes of earth and rust and old blood. Water drips somewhere in the black. Something breathes in the darkness.",
    [],
    {},
    {
        "chains": {
            "description": "Manacles dangle from the wall. Dried blood coats the metal. But some of it is fresh. Recent. Who was chained here?",
            "items": []
        },
        "corner": {
            "description": "Something moves in the corner - quick and wrong. You hear it skitter away on too many legs. The sound echoes impossibly.",
            "items": []
        },
        "warning": {
            "description": """Words carved into the stone wall:

'TURN BACK
NOT READY
NEED THREE THINGS
CRUCIFIX - KNIFE - BOOK
TOGETHER OR DIE'

The letters are carved deep, desperately.""",
            "items": []
        },
        "final message": {
            "description": """Papers scattered on the floor, stained dark:

'FINAL ENTRY - Graeme Crampton - October 31st, 1952

I'm going to face it. I have the three items.
The CRUCIFIX to ward it off.
The KNIFE to strike it down.
The ANCIENT BOOK to bind it forever.

If you're reading this, I failed.

You need ALL THREE ITEMS to defeat what's down here.
Without them, you will die.

The door requires the RUSTY KEY from the kitchen.

Tell Margaret I'm sorry. Tell Sarah I love-'

[The writing ends in a long streak of blood]""",
            "items": []
        }
    }
)

attic = Room(
    "Attic",
    "The attic is cramped and cold. Moonlight filters through a single grimy window. Dusty sheets cover old furniture, creating twisted silhouettes. A porcelain doll sits in the corner, its glass eyes reflecting the light. A heavy locked box sits in the center of the room.",
    [],
    {},
    {
        "boxes": {
            "description": "Old photographs spill from opened boxes. Family photos from happier times. But every single face has been violently scratched out. Every. Single. One.",
            "items": []
        },
        "window": {
            "description": "You look out at dark trees and storm clouds. Fresh air seeps through cracks in the glass. For just a moment, you remember what it's like to be outside. To be free.",
            "items": []
        },
        "doll": {
            "description": "The porcelain doll sits perfectly still. Then its head turns. Slowly. Deliberately. To look directly at you. Its painted smile never moves.",
            "items": [],
            "health": -1
        },
        "locked box": {
            "description": "A heavy wooden box bound with iron. A thick padlock seals it shut. You'll need something strong to break it open - like a CROWBAR.",
            "items": [],
            "action": "use_crowbar"
        },
        "cassette tape": {
            "description": "An old cassette tape sits on a small table with a hand-written label: 'FOR GRAEME - PLAY IN LIBRARY'",
            "items": ["cassette tape"],
            "examined_description": "The tape is gone from the table. Only dust remains."
        }
    }
)

second_floor_hall = Room(
    "Second Floor Hall",
    "The corridor stretches impossibly long in both directions. Doors line the walls - bedrooms, bathroom, utility. The carpet beneath your feet is threadbare and stained dark. Portraits of the Crampton family watch you pass, their expressions changing when you're not looking.",
    [],
    {},
    {
        "portraits": {
            "description": "The people in the paintings age as you watch. Their expressions shift from joy to fear to despair. They're not smiling anymore. They're warning you.",
            "items": []
        },
        "carpet": {
            "description": "Wet footprints appear on the carpet as you watch. Small ones. Child-sized. They lead from nowhere to nowhere. The prints are fresh. Still dripping.",
            "items": []
        },
        "hidden note": {
            "description": """A note hidden under loose carpet:

'Day 6 - Jacob writing

The children's room is dangerous. Whatever you do,
don't wind up the music box. I made that mistake.
Last night I heard it playing by itself.

This morning, Thomas was gone. We searched everywhere.
Graeme found him in the basement. What was left of him.

The master bedroom has protection. Margaret's CRUCIFIX.
It helped her sleep through the whispers.
I don't think any of us will sleep again.

The UTILITY ROOM has tools. Maybe something useful.
Maybe something to help us break out.

God help us all. - Jacob, October 30th, 1952'""",
            "items": []
        }
    }
)

master_bedroom = Room(
    "Master Bedroom",
    "A large four-poster bed dominates the room, its curtains hanging in tatters. A wardrobe stands against one wall, its doors slightly ajar. The air here is colder than the rest of the house. Your breath comes out in small clouds that linger.",
    [],
    {},
    {
        "bed": {
            "description": "The sheets are stained with dark, dried blood. The pillow has an indentation, as if someone's head just lifted moments ago. When you touch it, the bed is still warm.",
            "items": []
        },
        "mirror": {
            "description": "A full-length mirror stands in the corner. Your reflection moves a second too late. It smiles when you're not smiling. Its eyes are black.",
            "items": []
        },
        "wardrobe": {
            "description": "A large wooden wardrobe. The doors creak as they move. Something might be inside... or something might be waiting.",
            "items": [],
            "action": "search_wardrobe"
        },
        "letter": {
            "description": """A letter on the dresser, never sent:

'My Dearest Elizabeth,

By the time anyone reads this, we will be gone.
The Crampton Estate has claimed us, as it has claimed 
so many others before.

We tried to leave. God knows we tried.
But the house... it doesn't let go.
The doors lock. The windows won't break.
And the thing in the basement... it's spreading.

If you value your life, never come looking for us.
Let the house keep its dead.

The children miss you. Sarah asks about you every day.
I tell her you're coming. I lie to my own daughter.
Because I know we're never leaving this place.

Tell Graeme's brother we're sorry. Tell him to stay away.

The CRUCIFIX in the wardrobe is blessed. It protects.
But not forever. Nothing lasts forever here.

I'm so sorry. I'm so, so sorry.

Forever yours,
Margaret Crampton'""",
            "items": []
        }
    }
)

kids_bedroom = Room(
    "Kids Bedroom",
    "Toys are scattered across the floor as if a child just stopped playing mid-game. Two small beds sit against opposite walls, covers pulled back. A music box rests on a shelf, its ballerina frozen mid-spin. The room smells like dust and something sweet and cloying.",
    [],
    {},
    {
        "toys": {
            "description": "You blink. When your eyes open, the toys have moved. They're arranged in a circle now. All facing you. Watching.",
            "items": []
        },
        "closet": {
            "description": "You hear breathing from inside the closet. Slow, steady breathing. In and out. The breathing matches yours exactly. Perfectly synchronized.",
            "items": []
        },
        "music box": {
            "description": "A delicate music box with a spinning ballerina. Something tells you NOT to wind it up. The last person who did... didn't survive.",
            "items": [],
            "health": -2
        },
        "drawing": {
            "description": """A child's drawing in crayon:

A crude house drawn in black.
Stick figures with X's for eyes scattered around it.
One figure stands in an upstairs window.
It has too many eyes. Too many arms.
Drawn in red crayon.

In a child's handwriting at the bottom:
'our frend in the atik'
(The 'k' is backwards)

Next to it, in adult handwriting:
'Sarah drew this the day before she disappeared.
 She said her "friend" taught her how.
 I found this under her pillow.
 I found blood on the pillow too.
 - Margaret'"""
        }
    }
)

bathroom = Room(
    "Bathroom",
    "A small bathroom with cracked tiles and peeling wallpaper. The mirror is fogged despite the cold. A bathtub sits against the wall, rust-stained and filled with murky water. A small opening in the ceiling leads up to the attic.",
    [],
    {},
    {
        "cabinet": {
            "description": "A mirrored cabinet above the sink. Inside you find a dusty bandage, still sealed.",
            "items": ["bandage"],
            "examined_description": "The cabinet is empty now, just expired medications remain."
        },
        "bath": {
            "description": "The bathtub is filled with dark water. Something floats beneath the surface - you can't quite make it out. The water ripples though nothing touched it.",
            "items": []
        },
        "mirror": {
            "description": "The bathroom mirror is completely fogged over. You wipe it with your hand. Your reflection stares back... with blood running down its face. You don't have any blood on your face.",
            "items": []
        },
        "attic access": {
            "description": "A small square opening in the ceiling. A pull-down ladder leads up to the attic. Darkness seems to seep down from above.",
            "items": []
        }
    }
)

utility_room = Room(
    "Utility Room",
    "A cramped utility room filled with old tools and supplies. Shelves line the walls, stacked with paint cans and rusty equipment. A workbench sits in the corner. The air smells of oil and metal.",
    [],
    {},
    {
        "toolbox": {
            "description": "An old metal toolbox covered in rust. Inside, most tools are broken or rusted through. But you find a heavy CROWBAR in decent condition.",
            "items": ["crowbar"],
            "examined_description": "The toolbox is empty now except for broken screwdrivers and bent wrenches."
        },
        "shelf": {
            "description": "Dusty shelves stacked with old paint cans. Some have leaked, creating dark stains on the floor. The stains look almost like handprints.",
            "items": []
        },
        "workbench": {
            "description": "A wooden workbench with various tools scattered across it. Most are useless. But there's a note pinned to the wall above it.",
            "items": []
        },
        "maintenance log": {
            "description": """A maintenance log, written in neat handwriting:

'Crampton Estate - Maintenance Notes
Jacob Harris, Groundskeeper

October 15th, 1952:
Fixed leak in kitchen. Mr. Crampton seemed distracted.

October 20th, 1952:
Strange sounds from basement. Mr. Crampton says not to worry.
CROWBAR in utility room if needed for repairs.

October 25th, 1952:
The boy Thomas is missing. Mrs. Crampton won't stop crying.
Something is wrong in this house.

October 28th, 1952:
I tried to leave. The front door won't open.
I'm trapped here with them.

The CROWBAR might break us out. Or break open that
box in the attic. Graeme kept saying something was
hidden up there. Something important.

God, I just want to go home.

[The rest of the pages are blank]'""",
            "items": []
        }
    }
)

dining_room = Room(
    "Dining Room",
    "A long oak table dominates the room, still set as if waiting for dinner guests who never arrived. Place settings sit untouched - plates, glasses, silverware all positioned perfectly. Candles have melted into grotesque shapes. The air is heavy with the smell of decay.",
    [],
    {},
    {
        "table": {
            "description": "Deep scratch marks cover the wooden surface. Four parallel lines, like fingers clawing desperately. Someone was trying to hold on to something. Or trying to escape something.",
            "items": []
        },
        "sideboard": {
            "description": "A tall cabinet with tarnished silver handles. Inside, you find old silverware and a LOCKPICK tucked in a drawer.",
            "items": ["lockpick"],
            "examined_description": "The sideboard is empty now, just dusty china and broken glasses."
        },
        "candles": {
            "description": "The candles have melted into twisted, reaching shapes. Like frozen fingers grasping upward. When you get close, they're still warm. Still burning without flame.",
            "items": []
        },
        "place settings": {
            "description": """Each plate has a name card:

'Graeme Crampton' - Head of table
'Margaret Crampton' - Opposite end
'Thomas Crampton' - Left side
'Sarah Crampton' - Right side

A fifth card sits in the center of the table, blank.
Waiting for a name.
Waiting for you.""",
            "items": []
        }
    }
)

living_room = Room(
    "Living Room",
    "A once-comfortable room now filled with decay and shadow. A cold fireplace stands against one wall, its mantle covered in dust. A leather sofa sits beneath a curtained window. Family photographs line the walls, their frames tilted at odd angles.",
    [],
    {},
    {
        "fireplace": {
            "description": "The fireplace is cold and dark. Ash is piled high in the hearth. Among the ash, something glints - a small brass key.",
            "items": ["small key"],
            "examined_description": "The fireplace contains only ash now. Dead and cold."
        },
        "sofa": {
            "description": "A worn leather sofa with cracked cushions. You lift one cushion and find something wedged deep inside - a wooden CRUCIFIX on a chain.",
            "items": ["crucifix"],
            "examined_description": "The sofa is empty now, just old leather and broken springs."
        },
        "photographs": {
            "description": "Family photos cover the walls. The Cramptons in happier times. But every single face has been scratched out. Methodically. Violently. Someone took their time doing this.",
            "items": []
        },
        "family note": {
            "description": """A note tucked behind a photograph frame:

'To whoever finds this,

This room was where we gathered. Where we felt safe.
Before the basement. Before everything went wrong.

The SMALL KEY in the fireplace opens the conservatory door.
But don't go to the garden. Please. Don't make our mistake.

We went out there looking for Sarah.
We found things in the garden.
Bodies. So many bodies.

It hunts in the garden. 
If you go outside, it will find you.

Stay inside. Find the RUSTY KEY. Face what's in the basement.
That's the only way to end this.

- Margaret, October 30th, 1952'""",
            "items": []
        }
    }
)

conservatory = Room(
    "Conservatory",
    "A glass-walled room that was once beautiful, now overrun with dead plants. Vines have withered to black. Flowers are dried husks. Moonlight streams through cracked panes, casting twisted shadows. A heavy door leads to the back garden, sealed with a sturdy lock.",
    [],
    {},
    {
        "dead plants": {
            "description": "Dead vines and flowers cover every surface. They crumble to dust at your touch. But wait - one plant still lives. A single white flower glowing faintly in the darkness.",
            "items": []
        },
        "garden door": {
            "description": "A heavy oak door reinforced with iron bars. It's locked tight with a brass lock. You'll need the SMALL KEY to open it. But do you really want to?",
            "items": [],
            "action": "garden_door"
        },
        "gardener's log": {
            "description": """A weathered journal on a potting bench:

'Gardener's Log - Crampton Estate

October 1st, 1952:
All the plants died overnight. Every single one.
The house is poisoning the soil somehow.

October 10th, 1952:
Something walks in the garden at night.
I've seen it. Tall. Wrong shape. Too many limbs.
I told Mr. Crampton. He just stared at me.

October 15th, 1952:
Found bodies in the garden. Old bones. New bones.
This has been happening for years. Decades maybe.
The garden FEEDS it.

October 20th, 1952:
Don't go outside. NEVER GO OUTSIDE.
The SMALL KEY opens this door but it's a trap.
The garden is death.

[The final entry is just repeated words:]
DON'T GO OUT DON'T GO OUT DON'T GO OUT'""",
            "items": []
        }
    }
)

# Set up room connections based on Phasmophobia-style layout
grand_hall.neighbors = {
    "north": library,
    "east": dining_room,
    "west": living_room,
    "up": second_floor_hall
}

kitchen.neighbors = {
    "north": dining_room,
    "south": conservatory
}

dining_room.neighbors = {
    "south": kitchen,
    "west": grand_hall
}

library.neighbors = {
    "south": grand_hall,
    "down": basement
}

basement.neighbors = {
    "up": library
}

living_room.neighbors = {
    "east": grand_hall
}

conservatory.neighbors = {
    "north": kitchen
}

second_floor_hall.neighbors = {
    "down": grand_hall,
    "north": kids_bedroom,
    "east": master_bedroom,
    "south": bathroom,
    "west": utility_room
}

master_bedroom.neighbors = {
    "west": second_floor_hall,
    "up": attic
}

kids_bedroom.neighbors = {
    "south": second_floor_hall
}

bathroom.neighbors = {
    "north": second_floor_hall,
    "up": attic
}

utility_room.neighbors = {
    "east": second_floor_hall
}

attic.neighbors = {
    "down": bathroom
}

# Game loop functions
def show_room_menu(game):
    # Display room-specific action menu
    room = game.current_room
    choices = []
    
    # Always available actions
    choices.append(("View map", "map"))
    choices.append(("Check inventory", "inventory"))
    choices.append(("Show stats", "stats"))
    
    # Movement options
    if room.neighbors:
        choices.append(("Movement options", "movement"))
    
    # Examine objects
    if room.objects:
        choices.append(("Examine objects", "examine"))
    
    # Room-specific interactions
    room_actions = {
        "Kitchen": ("Search cupboard for supplies", "search_kitchen"),
        "Library": ("Use cassette player", "cassette_player"),
        "Basement": ("Use rusty key on hidden door", "use_key"),
        "Conservatory": ("Try garden door", "garden_door"),
        "Master Bedroom": ("Search wardrobe", "search_wardrobe"),
        "Attic": ("Use crowbar on locked box", "use_crowbar"),
        "Kids Bedroom": ("Meditate to recover sanity", "meditate")
    }
    
    if room.name in room_actions:
        choices.append(room_actions[room.name])
    
    # Rest option (once per room)
    if room.name not in game.used_life_bonus:
        choices.append(("Rest and recover", "rest"))
    
    return choices

def handle_movement_menu(game):
    # Handle movement submenu
    room = game.current_room
    choices = []
    
    direction_names = {
        "north": "North",
        "south": "South",
        "east": "East",
        "west": "West",
        "up": "Upstairs/Up",
        "down": "Downstairs/Down"
    }
    
    for direction, next_room in room.neighbors.items():
        dir_name = direction_names.get(direction, direction.title())
        choices.append((f"Go {dir_name} to {next_room.name}", direction))
    
    choices.append(("Back to main menu", "back"))
    
    return choices

def handle_examine_menu(game):
    # Handle examine submenu
    room = game.current_room
    choices = []
    
    for obj_name in room.objects.keys():
        choices.append((f"Examine {obj_name}", obj_name))
    
    choices.append(("Back to main menu", "back"))
    
    return choices

def print_menu(choices):
    # Print menu choices with letter shortcuts - QUICK
    letters = [chr(i) for i in range(ord('a'), ord('a') + len(choices))]
    for letter, (description, _) in zip(letters, choices):
        quick_print(f"  {letter}) {description}")
    return letters

def get_choice(letters):
    # Get valid choice from player
    while True:
        choice = input("\n> ").strip().lower()
        if choice in letters:
            return letters.index(choice)
        quick_print("Invalid choice. Please try again.")

def handle_action(game, action_code):
    # Handle special action codes
    if action_code == "map":
        game.show_map()
        
    elif action_code == "inventory":
        if not game.inventory:
            quick_print("Your pockets are empty. You have nothing.")
        else:
            quick_print("You check your pockets:")
            for item in game.inventory:
                quick_print(f"  - {item}")
    
    elif action_code == "stats":
        game.show_stats()
    
    elif action_code == "rest":
        game.gain_life(1)
        slow_print("You take a moment to compose yourself.")
        slow_print("Your racing heart begins to slow.")
        
    elif action_code == "search_kitchen":
        search_cupboard(game)
        
    elif action_code == "cassette_player":
        use_cassette_player(game)
        
    elif action_code == "use_crowbar":
        use_crowbar_on_box(game)
        
    elif action_code == "use_key":
        if "rusty key" not in game.inventory:
            slow_print("You need a key to unlock the hidden door.")
            slow_print("The door remains sealed. Mocking you.")
            game.lose_sanity(3)
        else:
            slow_print("The RUSTY KEY slides into a hidden lock in the wall.")
            slow_print("Metal scrapes against metal. The lock clicks loudly.")
            slow_print("A door swings open, revealing stairs descending into darkness.")
            slow_print("")
            time.sleep(1)
            slow_print("Cold air rushes up from below. You hear something breathing.")
            slow_print("This is it. Whatever haunts this place waits below.")
            slow_print("The thing that killed Graeme. That killed them all.")
            slow_print("")
            time.sleep(1)
            
            quick_print("Do you descend to face what waits in the darkness?")
            quick_print("  a) Yes, it's time to end this")
            quick_print("  b) No, not yet - I need to prepare")
            
            choice = input("\n> ").strip().lower()
            if choice == 'a':
                result = boss_fight(game)
                if not result:
                    game.game_over = True
                return result
            else:
                slow_print("You step back from the darkness. Your courage falters.")
                slow_print("Not yet. You're not ready yet.")
                
    elif action_code == "garden_door":
        if "small key" not in game.inventory:
            slow_print("The garden door is locked with a brass lock.")
            slow_print("You need the SMALL KEY to open it.")
            game.lose_sanity(2)
        else:
            slow_print("You unlock the garden door with the SMALL KEY.")
            slow_print("The lock clicks. Cold wind rushes in.")
            slow_print("You push the door open and step outside...")
            slow_print("")
            time.sleep(1)
            slow_print("Bodies. Dozens of them. Pale and lifeless.")
            slow_print("They're scattered across the overgrown grass.")
            slow_print("Some are old - just bones. Others are fresh. Recent.")
            slow_print("Their eyes stare blankly at the storm-dark sky.")
            slow_print("")
            time.sleep(1)
            slow_print("A shadow moves between the trees. Fast. Inhuman.")
            slow_print("It sees you. It's coming for you!")
            slow_print("You slam the door and lock it, gasping for breath.")
            slow_print("Something SLAMS against the door from outside.")
            slow_print("Again. And again. And again.")
            slow_print("Then... silence.")
            game.lose_sanity(20)
            game.lose_life(1, "The terror costs you dearly. Your hands won't stop shaking.")
            
    elif action_code == "search_wardrobe":
        search_wardrobe(game)
        
    elif action_code == "meditate":
        outcomes = [
            ("You close your eyes and breathe deeply. Peace washes over you.", lambda: game.gain_sanity(15)),
            ("As you meditate, you hear a child's laughter. Not threatening. Comforting.", lambda: game.gain_life(1)),
            ("You feel a small hand take yours gently. When you open your eyes, you're alone.", lambda: game.gain_sanity(10)),
            ("Something whispers in your ear: 'Run. Run now.' You jolt awake, heart pounding.", lambda: game.lose_sanity(5))
        ]
        outcome = random.choice(outcomes)
        slow_print(outcome[0])
        outcome[1]()
    
    return None

def game_loop(game):
    # Main game loop
    slow_print("="*75)
    slow_print("        WELCOME TO THE CRAMPTON ESTATE")
    slow_print("="*75)
    slow_print("")
    time.sleep(1)
    slow_print("The storm outside rages as you stumble through the front door.")
    slow_print("Lightning flashes. Thunder rolls.")
    slow_print("Behind you, the door slams shut on its own.")
    slow_print("You hear the lock click. Once. Twice. Three times.")
    slow_print("")
    time.sleep(1)
    slow_print("There's no going back the way you came.")
    slow_print("The house has you now.")
    slow_print("")
    time.sleep(1)
    slow_print("Your only hope is to find another way out.")
    slow_print("But the Crampton Estate doesn't let people leave.")
    slow_print("It hasn't for decades.")
    slow_print("")
    time.sleep(1)
    slow_print("Move quickly. The house feeds on hesitation.")
    slow_print("Watch your sanity. Watch your health.")
    slow_print("Read the notes. Learn what happened here.")
    slow_print("And whatever you do...")
    slow_print("Don't let the darkness win.")
    slow_print("")
    time.sleep(1)
    quick_print("Type '?' at any main menu for help.")
    slow_print("="*75)
    
    input("\nPress Enter to begin your nightmare...")
    
    while not game.game_over:
        game.update_room_visit()
        
        # Passive sanity drain
        if game.passive_sanity_drain():
            break
        
        # Display current status
        print("\n" + "="*75)
        game.current_room.describe()
        print("-"*75)
        game.show_stats()
        print("="*75)
        
        # Show main menu
        quick_print("\nWhat will you do?")
        choices = show_room_menu(game)
        letters = print_menu(choices)
        quick_print("  ?) Help")
        
        choice_input = input("\n> ").strip().lower()
        
        if choice_input == '?':
            show_help()
            continue
            
        if choice_input not in letters:
            quick_print("Invalid choice. Please try again.")
            game.lose_sanity(2, "Hesitation. Every second counts. The house is watching.")
            continue
        
        idx = letters.index(choice_input)
        action_type = choices[idx][1]
        
        # Handle movement submenu
        if action_type == "movement":
            quick_print("\nWhere do you want to go?")
            move_choices = handle_movement_menu(game)
            move_letters = print_menu(move_choices)
            move_idx = get_choice(move_letters)
            
            direction = move_choices[move_idx][1]
            if direction == "back":
                continue
            
            game.current_room = game.current_room.neighbors[direction]
            slow_print(f"\nYou move {direction}...")
            slow_print("The floorboards creak under your weight.")
            slow_print("Somewhere in the house, something stirs.")
            time.sleep(0.5)
            
        # Handle examine submenu
        elif action_type == "examine":
            quick_print("\nWhat do you want to examine?")
            exam_choices = handle_examine_menu(game)
            exam_letters = print_menu(exam_choices)
            exam_idx = get_choice(exam_letters)
            
            obj_name = exam_choices[exam_idx][1]
            if obj_name == "back":
                continue
            
            # Check for special actions
            obj_info = game.current_room.objects.get(obj_name)
            if obj_info and obj_info.get("action"):
                action = obj_info["action"]
                if action == "search_cupboard":
                    search_cupboard(game)
                elif action == "search_wardrobe":
                    search_wardrobe(game)
                elif action == "use_cassette_player":
                    use_cassette_player(game)
                elif action == "use_crowbar":
                    use_crowbar_on_box(game)
                elif action == "garden_door":
                    handle_action(game, "garden_door")
            else:
                examine_object(game, obj_name)
            
        # Handle special actions
        else:
            result = handle_action(game, action_type)
            if result is True:  # Escaped/won
                break
        
        # Check for death
        if game.lives <= 0 or game.sanity <= 0:
            game.game_over = True
            break
        
        # Check for victory
        if game.escaped and game.boss_defeated:
            show_victory(game)
            break
        
        time.sleep(0.3)
    
    # Game over
    if game.game_over and not game.escaped:
        show_game_over(game)

def show_help():
    # Display help information - QUICK PRINT
    quick_print("\n" + "="*75)
    quick_print("                           GAME HELP")
    quick_print("="*75)
    quick_print("")
    quick_print("OBJECTIVE:")
    quick_print("  Escape the Crampton Estate alive by defeating what lurks below.")
    quick_print("")
    quick_print("STATS:")
    quick_print("  HEALTH (♥): Your life force. Reach 0 and you die.")
    quick_print("  SANITY (█): Your mental state. Reach 0 and madness takes you.")
    quick_print("")
    quick_print("TIPS:")
    quick_print("  - Examine EVERYTHING - items and notes reveal the truth")
    quick_print("  - Read all notes carefully - they contain vital information")
    quick_print("  - You need THREE ITEMS to defeat the basement creature")
    quick_print("  - The ATTIC has secrets - find the CROWBAR first")
    quick_print("  - Rest when you can to recover health (once per room)")
    quick_print("  - Don't linger too long - sanity drains over time")
    quick_print("  - The GARDEN is death - avoid it if possible")
    quick_print("")
    quick_print("KEY ITEMS TO FIND:")
    quick_print("  - CROWBAR: In Utility Room - opens attic box")
    quick_print("  - RUSTY KEY: In Kitchen cupboard - opens basement door")
    quick_print("  - CRUCIFIX: Protects from supernatural harm")
    quick_print("  - KNIFE: Weapon against darkness")
    quick_print("  - ANCIENT BOOK: Contains binding ritual")
    quick_print("  - CASSETTE TAPE: Play in library for important clues")
    quick_print("")
    quick_print("=" *75)
    input("\nPress Enter to continue...")

def show_victory(game):
    # Display victory screen
    slow_print("\n" + "="*75)
    slow_print("                         V I C T O R Y")
    slow_print("="*75)
    slow_print("")
    time.sleep(1)
    slow_print("You climb the basement stairs, your legs shaking.")
    slow_print("The house is different now. Lighter. Quieter.")
    slow_print("The oppressive darkness has lifted like morning fog.")
    slow_print("")
    time.sleep(1)
    slow_print("You make your way through the silent halls.")
    slow_print("The portraits no longer watch you. They're just paintings now.")
    slow_print("The whispers have stopped. The house breathes easy.")
    slow_print("")
    time.sleep(1)
    slow_print("The front door stands before you.")
    slow_print("It opens easily now, as if the house is letting you go.")
    slow_print("Releasing you from its grip.")
    slow_print("You step out into the cold night air.")
    slow_print("")
    time.sleep(1)
    slow_print("Behind you, the Crampton Estate stands silent.")
    slow_print("The windows are dark. No shadows move within.")
    slow_print("The curse is broken. The Cramptons can finally rest.")
    slow_print("")
    time.sleep(1)
    slow_print("But you know you'll never be the same.")
    slow_print("The memories will haunt you forever.")
    slow_print("You've seen things no one should see.")
    slow_print("You've survived. But at what cost?")
    slow_print("")
    slow_print("="*75)
    quick_print(f"\nFINAL STATISTICS:")
    quick_print(f"  Lives Remaining: {game.lives}/{game.max_lives}")
    quick_print(f"  Sanity Remaining: {game.sanity}/100")
    quick_print(f"  Rooms Explored: {game.survived_count}")
    quick_print(f"  Items Collected: {len(game.inventory)}")
    quick_print(f"  Notes Read: {len([n for n in game.notes_read if n != 'tape_played'])}")
    quick_print("")
    slow_print("You survived the Crampton Estate.")
    slow_print("You defeated the darkness.")
    slow_print("But the house will always remember you...")
    slow_print("And you will always remember it.")
    slow_print("="*75)

def show_game_over(game):
    # Display game over screen
    slow_print("\n" + "="*75)
    slow_print("                      G A M E   O V E R")
    slow_print("="*75)
    slow_print("")
    
    if game.sanity <= 0:
        slow_print("The madness consumed you.")
        slow_print("Your mind shattered like glass.")
        slow_print("The whispers are all that remain now.")
        slow_print("You are part of the house. Forever.")
    else:
        slow_print("Your vision fades to black.")
        slow_print("The cold embrace of death takes you.")
        slow_print("The house claims another victim.")
        slow_print("Another soul to add to its collection.")
    
    slow_print("")
    slow_print("="*75)
    quick_print(f"\nYOUR JOURNEY:")
    quick_print(f"  Rooms Explored: {game.survived_count}")
    quick_print(f"  Final Health: {game.lives}/{game.max_lives}")
    quick_print(f"  Final Sanity: {game.sanity}/100")
    quick_print(f"  Items Found: {', '.join(game.inventory) if game.inventory else 'None'}")
    quick_print(f"  Notes Read: {len([n for n in game.notes_read if n != 'tape_played'])}")
    quick_print("")
    slow_print("The Crampton Estate claims another soul.")
    slow_print("Another name carved into its walls.")
    slow_print("Another whisper in the darkness...")
    slow_print("Another ghost in the halls.")
    slow_print("")
    slow_print("The house always wins in the end.")
    slow_print("="*75)

# Main execution
if __name__ == "__main__":
    quick_print("\nInitializing Crampton Estate...")
    time.sleep(0.5)
    quick_print("Loading saved souls...")
    time.sleep(0.5)
    quick_print("Opening the door...")
    time.sleep(0.5)
    print()
    
    game = GameState(grand_hall)
    game_loop(game)