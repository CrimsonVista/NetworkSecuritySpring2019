
def fib_infinity():
    print("Position 1")
    yield 1
    print("Position 2")
    yield 1
    x,y = 1, 1
    counter = 3
    while True:
        print("Position",counter)
        counter += 1
        z = x+y
        yield z
        x = y
        y = z

if __name__=="__main__":
    import sys
    n = int(sys.argv[1])
    fib_generator = fib_infinity()
    for i in range(n):
        print(next(fib_generator))