
def fib_infinity():
    yield 1
    yield 1
    x,y = 1, 1
    for i in range(2,n):
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