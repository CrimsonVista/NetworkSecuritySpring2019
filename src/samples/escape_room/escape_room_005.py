import random

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

    room_template1 = """You are in a locked room. There is only one door
and it has a numeric keypad (keypad:{_door_code}). Above the door is a clock that reads {_clock_time}."""

    def __init__(self):
        self.state = {}
        self.playerInventory = set([])
        
    def _advanceClock(self):
        self.state["clock"].values["time"] -= 1
        
    def _cmd_look(self, lookParts):
        if len(lookParts) == 0:
            visibleState = {}
            visibleState.update(self.state)
            for object in self.state:
                for key in self.state[object].values.keys():
                    visibleState["_{}_{}".format(object, key)] = self.state[object].values[key]
            roomView = self.room_template1.format(**visibleState)
            
            return roomView
        object = lookParts[-1]
        
        if object not in self.state or "visible" not in self.state[object].attrs:
            return "You don't see that here."
        
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
            
        if "code" in self.state[object].values:
            if len(unlocker) != 4:
                return "The code must be 4 digits"
            try:
                inputCode = int(unlocker)
            except:
                return "That's not a valid code"
            if inputCode != self.state[object].values["code"]:
                return "That is not the right code!"
            
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
            
        return "You open the {}".format(object)
        
    def start(self):
        self.state = {
            "door": ObjectState("door", "visible", "closed", "locked", code=random.randint(0,9999)),
            "clock": ObjectState("clock", "visible", time=100),
        }
        self.state["door"].values["description"] = "The door is strong and highly secured. The door is locked and requires a 4-digit code to open."
                
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
        
def main():
    room = EscapeRoom()
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
    main()