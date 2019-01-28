
door = "closed"
while door == "closed":
    command = input(">> ")
    if command == "open door":
        print("you open the door")
        door = "open"
    else:
        print("you don't know how to do that.")
print("congrautlations! You escaped")