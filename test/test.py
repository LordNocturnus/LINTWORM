

def test_function(inp1, inp2="([{",  # this is a test
                  inp3=max(0, 100)):
    """
    This is a test function for formatting checks
    testing the new line in explanations

    :param inp1: {type} explanation
                        works with multiline aswell
    :param inp2: {type} explanation
    :param inp3: {type} explanation

    :return: {type}
    :return: {type}

    :raise: ValueError
    """
    if inp1:
        return inp1
    elif inp2 == "([{":
        raise ValueError
    return inp2
