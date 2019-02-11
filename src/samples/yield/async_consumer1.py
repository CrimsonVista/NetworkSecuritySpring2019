import asyncio, random

global_queue = []

async def generate_numbers():
    while True:
        print("Inside generate")
        # only generate a random number on 50/50 odds
        dice_roll = random.random()
        print("\tRandom Number:", dice_roll)
        if dice_roll < .5:
            rnum  = random.randint(0,1000)
            print("\tInserting random number: ", rnum)
            global_queue.append(rnum)
        else:
            print("Too lazy this time. maybe next time.")
        print("DONE WITH GENERATOR")
        await asyncio.sleep(1)
        
async def running_average():
    queue_index = 0
    sum = 0
    average = 0
    while True:
        print("Inside running average. Check for updates")
        if queue_index >= len(global_queue):
            print("\tNothing new. Go back to sleep!")
        else:
            new_numbers = len(global_queue) - queue_index
            print("\tGot {} new numbers!".format(new_numbers))
            for i in range(queue_index, len(global_queue)):
                sum += global_queue[i]
            queue_index += new_numbers
            average = sum/len(global_queue)
            print("New sum: ", sum)
            print("New running average: ", average)
        print("DONE WITH CONSUMER")
        await asyncio.sleep(1)
        
async def shutdown_after(queue_size):
    while len(global_queue) < queue_size:
        await asyncio.sleep(1)
    print("Global queue now size {}. shutting down.".format(len(global_queue)))
    asyncio.get_event_loop().stop()

if __name__=="__main__":
    asyncio.ensure_future(generate_numbers())
    asyncio.ensure_future(running_average())
    asyncio.ensure_future(shutdown_after(queue_size=15))
    asyncio.get_event_loop().run_forever()
    asyncio.get_event_loop().close()
                