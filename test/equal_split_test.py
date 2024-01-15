def split_list_into_chunks(lst, n):
    """
    Splits a list into n roughly equal-sized chunks.

    Parameters:
    lst (list): The list to be split.
    n (int): The number of chunks to split the list into.

    Returns:
    list of lists: n chunks from the original list.
    """
    # Calculate the size of each chunk
    chunk_size, remainder = divmod(len(lst), n)

    # Initialize variables
    chunks = []
    start = 0

    # Create each chunk
    for i in range(n):
        # If there are leftovers, distribute them among the first few chunks
        end = start + chunk_size + (1 if i < remainder else 0)
        chunks.append(lst[end-1])
        start = end

    return chunks


# Example usage
example_list = list(range(8))
number_of_chunks = 4

# Splitting the example list
print(split_list_into_chunks(example_list, number_of_chunks))
