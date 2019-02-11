
def fib_n(n):
    if n < 1:
        raise Exception("Parameter 'n' must be greater than 0")
    yield 1
    if n < 2:
        return
    yield 1
    last_two = [1,1]
    for i in range(2,n):
        x, y = last_two
        yield x+y
        last_two.pop(0)
        last_two.append(x+y)

if __name__=="__main__":
    import sys
    n = int(sys.argv[1])
    for fib_num in fib_n(n):
        print(fib_num)