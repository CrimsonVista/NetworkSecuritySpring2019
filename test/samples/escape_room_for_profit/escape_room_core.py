"""
10 object Room

Escape 1: Unlock door
  - Enter <number> in keypad
  - look painting
  - wear glasses
  - hang painting backwards
  - get glasses from hole
  - pry board with hammer
  - get hammer from chest
  - open chest
  - unlock chest with hairpin
  - get hairpin from hair
  - look mirror
  
Escape 2: Blow up door
  - hit rock with hammer
  - put rock on trail
  - drag keg to door
  - hit keg with hammer
  - get rock
  - get hammer from chest
  - open chest
  - unlock chest with hairpin
  - get hairpin
  - look mirror
"""
import random, sys

class ObjectState:
    def __init__(self, name, *attrs, **values):
        self.name = name
        self.attrs = set(attrs)
        self.values = values
        self.inventoryState = {}
        
    def __repr__(self):
        if "short_description" in self.values:
            return str(self.values["short_description"])
        return self.name
        
        
def listFormat(l):
    l = ["a "+str(objectState) for objectState in l if "visible" in objectState.attrs]
    return ", ".join(l)
        
class EscapeRoom:

    cheat_room_template1 = """You are in a locked room. There is only one door
and it has a numeric keypad (keypad:{_door_code}). Above the door is a clock that reads {_clock_time}.
Across from the door is a large {mirror}. Below the mirror is an old chest.

The room is old and musty and the floor is creaky and warped."""

    room_template1 = """You are in a locked room. There is only one door
and it has a numeric keypad. Above the door is a clock that reads {_clock_time}.
Across from the door is a large {mirror}. Below the mirror is an old chest.

The room is old and musty and the floor is creaky and warped."""

    def __init__(self, cheat=False):
        self.state = {}
        self.playerInventory = set([])
        self.cheat = cheat
        
    def _advanceClock(self):
        self.state["clock"].values["time"] -= 1
        
    def _cmd_look(self, lookParts):
        if len(lookParts) == 0:
            visibleState = {}
            visibleState.update(self.state)
            for object in self.state:
                for key in self.state[object].values.keys():
                    visibleState["_{}_{}".format(object, key)] = self.state[object].values[key]
            template = self.cheat and self.cheat_room_template1 or self.room_template1
            roomView = template.format(**visibleState)
            
            return roomView
        object = lookParts[-1]
        
        if object not in self.state or "visible" not in self.state[object].attrs:
            return "You don't see that here."
        
        if "container" in self.state[object].attrs:
            if "in" == lookParts[0]:
                if "closed" in self.state[object].attrs:
                    return "You can't do that! It's closed!"
                return "Inside the {} you see: {}".format(object, listFormat(self.state[object].inventoryState.values()))
        
        for revealed in self.state[object].values.get("reveals", []):
            if revealed in self.state and "visible" not in self.state[revealed].attrs:
                self.state[revealed].attrs.add("visible")
        
        return self.state[object].values.get("description", "You see nothing special.")
        
    def _cmd_unlock(self, enterParts):
        if len(enterParts) == 0:
            return "That doesn't make sense!"
        if len(enterParts) == 1:
            return "Unlock {} with what?".format(enterParts[0])
        object = enterParts[0]
        unlocker = enterParts[-1]
        
        if object not in self.state or "visible" not in self.state[object].attrs:
            return "You don't see that here."
            
        if "unlocked" in self.state[object].attrs:
            return "It's already unlocked"
            
        if "locked" not in self.state[object].attrs:
            return "You can't unlock that!"
            
        if "unlockers" in self.state[object].values:
            if unlocker not in self.playerInventory:
                return "You don't have a {}".format(unlocker)
            if unlocker not in self.state[object].values["unlockers"]:
                return "It doesn't unlock."
        elif "code" in self.state[object].values:
            if len(unlocker) != 4:
                return "The code must be 4 digits"
            try:
                inputCode = int(unlocker)
            except:
                return "That's not a valid code"
            if inputCode != self.state[object].values["code"]:
                return "That's not the right code!"
            
        self.state[object].attrs.remove("locked")
        self.state[object].attrs.add("unlocked")
            
        return "You hear a click! It worked!"
        
    def _cmd_open(self, openParts):
        if len(openParts) == 0:
            return "Open what?"
            
        object = openParts[0]
        if object not in self.state or "visible" not in self.state[object].attrs:
            return "You don't see that."
            
        if "open" in self.state[object].attrs:
            return "It's already open!"
            
        if "closed" not in self.state[object].attrs:
            return "You can't open that!"
            
        if "locked" in self.state[object].attrs:
            return "It's locked"
            
        self.state[object].attrs.remove("closed")
        self.state[object].attrs.add("open")
            
        return "You open the {}.".format(object)

    def _cmd_get(self, getParts):
        if len(getParts) == 0:
            return "Get what?"
        object = getParts[0]
        if len(getParts) > 1:
            container = getParts[-1]
        else:
            container = None
            
        if container == None:
            getState = self.state
        elif container not in self.state or "container" not in self.state[container].attrs:
            return "You can't get something out of that!"
        elif "open" not in self.state[container].attrs:
            return "It's not open."
        else:
            getState = self.state[container].inventoryState

        if object not in getState or "visible" not in getState[object].attrs:
            return "You don't see that"
        if "gettable" not in getState[object].attrs:
            return "You can't get that."
        if "object" in self.playerInventory:
            return "You already have that."
        
        self.playerInventory.add(object)
        if object not in self.state:
            self.state[object] = getState[object]
            del getState[object]
        if object == "hairpin":
            self.state["mirror"].values["description"] = "You look in the mirror and see yourself"
        return "You got it."
        
    def _cmd_pry(self, pryParts):
        if len(pryParts) < 2:
            return "Pry what with what?"
        object = pryParts[0]
        tool = pryParts[-1]
        if object not in self.state or "visible" not in self.state[object].attrs:
            return "You don't see that"
        if "open" in self.state[object].attrs:
            return "It's already pried open."
        if tool not in self.playerInventory:
            return "You don't have a {}".format(tool)
        if "lever" not in self.state[tool].attrs: 
            return "There's no way that will pry anything open."
        
        self.state[object].attrs.add("open")
        if object == "board":
            self.state["board"].values["description"] = "The board has been pulled open. You can look inside."
        return "You use the {} to pry open the {}. It takes some work, but with some blood and sweat, you manage to get it open.".format(tool, object)
        
    def _cmd_wear(self, wearParts):
        if len(wearParts) == 0:
            return "Wear what?"
        object = wearParts[-1]
        if object not in self.state or "visible" not in self.state[object].attrs:
            return "You don't see that"
        if object not in self.playerInventory:
            return "You don't have a {}".format(object)
        if self.state[object].values["in_use"]:
            return "You're already wearing them!"
        
        self.state[object].values["in_use"] = True
        if object == "glasses":
            digits = [digit for digit in str(self.state["door"].values["code"])]
            while len(digits) < 4:
                digits = ["0"] + digits
            # remove duplicates
            digits = list(set(digits))
            # sort
            digits.sort()
            digitString = ",".join(digits)
            self.state["door"].values["description"] = "The door is strong and highly secured. The door is locked and requires a 4-digit code to open."
            self.state["door"].values["description"] += " But now you're wearing these glasses you notice something! There are smudges on the digits "
            self.state["door"].values["description"] += digitString + "."
        return "You are now wearing the {}.".format(object)
        
    def _cmd_inventory(self, inventoryParts):
        if len(inventoryParts) != 0:
            return "What?!"
        items = ", ".join(["a "+item for item in self.playerInventory])
        return "You are carrying {}".format(items)
        
    def start(self):
        self.state = {
            "door": ObjectState("door", "visible", "closed", "locked", code=random.randint(0,9999)),
            "clock": ObjectState("clock", "visible", time=100),
            "mirror": ObjectState("mirror", "visible", short_description="mirror", reveals=["hairpin"]),
            "hairpin": ObjectState("hairpin", "gettable"),
            "chest": ObjectState("chest", "container", "visible", "locked", "closed", unlockers=["hairpin"]),
            "floor": ObjectState("floor", "visible", reveals=["board"]),
            "board": ObjectState("board", "container", "pryable"),
        }
        self.state["door"].values["description"] = "The door is strong and highly secured. The door is locked and requires a 4-digit code to open."
        self.state["mirror"].values["description"] = "You look in the mirror and see yourself... wait, there's a hairpin in your hair. Where did that come from?"
        self.state["chest"].values["description"] = "An old chest. It looks worn, but it's still sturdy. And it's locked."
        self.state["chest"].inventoryState["hammer"] = ObjectState("hammer", "gettable", "visible", "lever")
        self.state["floor"].values["description"] = "The floor makes you nervous. It feels like it could fall in. One of the boards is loose."
        self.state["board"].values["description"] = "The board is loose, but won't come up when you pull on it. Maybe if you pried it open with something."
        self.state["board"].inventoryState["glasses"] = ObjectState("glasses", "visible", "gettable", "wearable", in_use=False)
        self.state["board"].inventoryState["glasses"].values["description"] = "These look like spy glasses. Maybe they reveal a clue!"
        
    def command(self, commandString):
        if commandString.strip == "":
            return ""
        commandParts = commandString.split(" ")
        function = "_cmd_"+commandParts[0]
        if not hasattr(self, function):
            return "You don't know how to do that."
        result = getattr(self, function)(commandParts[1:])
        self._advanceClock()
        if self.status() == "dead":
            result += "\nOh no! The clock starts ringing!!! After a few seconds, the room fills with a deadly gas..."        
        return result
        
    def status(self):
        if self.state["clock"].values["time"] <= 0:
            return "dead"
        elif "closed" in self.state["door"].attrs:
            return "locked"
        else: return "escaped"
        
def main(args):
    room = EscapeRoom(cheat=("--cheat" in args))
    room.start()
    while room.status() == "locked":
        command = input(">> ")
        output = room.command(command)
        print(output)
    if room.status() == "escaped":
        print("Congratulations! You escaped!")
    else:
        print("Sorry. You died.")
        
if __name__=="__main__":
    main(sys.argv[1:])