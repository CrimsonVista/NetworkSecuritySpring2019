
global_samples = []

def nonblocking_average(eventual_sample_count):
    sum = 0
    min_sample = None
    max_sample = None
    for index in range(eventual_sample_count):
        if index >= len(global_samples):
            yield "not finished"
        sample = global_samples[index]
        if min_sample == None or sample < min_sample:
            min_sample = sample
        if max_sample == None or sample > max_sample:
            max_sample = sample
        sum += sample
    yield (min_sample, max_sample, sum/eventual_sample_count)
    
if __name__=="__main__":
    student_count = int(input("How many students: "))
    for intermediate_result in nonblocking_average(student_count):
        if intermediate_result == "not finished":
            global_samples.append(int(input("Enter next score: ")))
        else:
            min_score, max_score, avg_score = intermediate_result
            print("Finished")
            print("Max Score: ", max_score)
            print("Min Score: ", min_score)
            print("Avg Score: ", avg_score)