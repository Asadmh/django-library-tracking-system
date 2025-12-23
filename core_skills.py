import random
# rand_list =
random_nums = [random.randint(1,20) for _ in range(10)]

# list_comprehension_below_10 =
filtered_nums = [x for x in random_nums if x < 10]

# list_comprehension_below_10 =
filtered_nums_using_filter = list(filter(lambda x: x < 10, random_nums))

print(random_nums)
print(filtered_nums)
print(filtered_nums_using_filter)