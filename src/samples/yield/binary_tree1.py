
class BinaryTreeNode:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left_subtree = left
        self.right_subtree = right
    
    def insert(self, new_value):
        if new_value < self.value:
            self._insert_left(new_value)
        else:
            self._insert_right(new_value)
            
    def _insert_left(self, new_value):
        if self.left_subtree == None:
            self.left_subtree = BinaryTreeNode(new_value)
        else:
            self.left_subtree.insert(new_value)
    
    def _insert_right(self, new_value):
        if self.right_subtree == None:
            self.right_subtree = BinaryTreeNode(new_value)
        else:
            self.right_subtree.insert(new_value)
            
    """
    def ugly_insert(self):
        if self.left_subtree:
            for value in self.left_subtree.iterate():
                yield value
        yield self.value
        if self.right_subtree:
            for value in self.right_subtree.iterate():
                yield value
    """
            
    def iterate(self):
        if self.left_subtree:
            yield from self.left_subtree.iterate()
        yield self.value
        if self.right_subtree:
            yield from self.right_subtree.iterate()
         
         
if __name__=="__main__":
    import random
    
    # 25 random numbers
    random_numbers = [random.randint(0,1000) for i in range(25)]
    binary_tree = BinaryTreeNode(random_numbers.pop(0))
    while random_numbers:
        binary_tree.insert(random_numbers.pop(0))
    for sorted_number in binary_tree.iterate():
        print(sorted_number)