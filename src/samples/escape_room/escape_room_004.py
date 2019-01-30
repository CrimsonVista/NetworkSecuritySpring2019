
def openCommand(openParts, locked):
    if len(openParts) == 0:
        print("Open what?")
        return "closed"
    object = openParts[0]
    if object == "door":
        if locked:
            print("you can't open the door! It's locked")
        else:
            print("you open the door")
            return "open"
    else:
        print("You don't know how to open that.")
    return "closed"
    
def unlockCommand(unlockParts, code):
    if len(unlockParts) <2:
        print("Unlock what with what?")
        return True
    object = unlockParts[0]
    code = unlockParts[-1]
    if object == "door":
        if code == str(code):
            print("That's the correct code! The door unlocks!")
            return False
        else:
            print("That's the wrong code!")
    else:
        print("You don't know how to unlock that.")
    return True

door = "closed"
locked = True
code = 1234
while door == "closed":
    command = input(">> ")
    commandParts = command.split(" ")
    command = commandParts[0]
    if command == "open":
        door = openCommand(commandParts[1:], locked)
    elif command == "unlock":
        locked = unlockCommand(commandParts[1:], code)
    else:
        print("you don't know how to do that.")
print("congrautlations! You escaped")