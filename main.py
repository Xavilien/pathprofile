

def checker(question, check):
    """Asks user a question and checks that the input is valid, if not ask again"""
    while True:
        output = raw_input(question)
        if check(output):
            return output


def main():
    radio = checker('What radio are you using? 408 or 406? ', lambda x: x in ['406', '408'])


if __name__ == '__main__':
    main()
