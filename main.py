def mgr_distance(mgr1, mgr2):
    """Calculate distance btween 2 mgrs"""
    mgr1 = map(lambda x: float(x)/10, mgr1.split())
    mgr2 = map(lambda x: float(x)/10, mgr2.split())
    distance = ((mgr1[0] - mgr2[0]) ** 2 + (mgr1[1] - mgr2[1]) ** 2) ** 0.5

    print(distance)

    return distance


def checker(question, check):
    """Asks user a question and checks that the input is valid, if not ask again"""
    while True:
        output = raw_input(question)
        if check(output):
            return output
        else:
            print("Not valid input")


def check_float(x):
    """Check if x is a float"""
    try:
        float(x)
        return True
    except ValueError:
        return False


def check_int(x):
    """Check if x is a int"""
    try:
        int(x)
        return True
    except ValueError:
        return False


def check_freq(radio, freq):
    """Check whether the frequency entered is valid"""
    try:
        freq = float(freq) * 100  # Make sure that the input is a float and multiply by 100 for easier checking
    except ValueError:
        return False

    if freq % 25 != 0:  # Check if the frequency is in multiples of 0.250 e.g. 1000.250 or 1000.500 not 1000.100
        return False

    # Check if frequency is within range
    if radio == 406 and freq not in range(61000, 96025, 25):
        return False
    elif radio == 408 and freq not in range(135000, 269025, 25):
        return False

    return True


def calculate_effective_object(obj1, obj2, distance):
    """Calculate the effective height and distance of the imaginary object created by 2 different objects in path"""
    grad1 = obj1[1]/obj1[0]
    grad2 = -obj2[1] / (distance-obj2[0])

    # eqn1 = lambda x: grad1 * x
    # eqn2 = lambda x: grad2 * x - grad2 * obj2[0] + obj2[1]

    d = (grad2 * obj2[0] - obj2[1]) / (grad2 - grad1)
    h = grad1 * d

    return d, h


def main():
    # Step 1: collect all the parameters for the formulas
    radio = int(checker('408 or 406? ', lambda r: r in ['406', '408']))
    freq = float(checker('Transmitting frequency? ', lambda f: check_freq(radio, f)))
    distance = float(checker('Total distance between the nodes(km)? ', check_float))
    ht = float(checker('Height of transmitting node in metres? ', check_float))
    hr = float(checker('Height of receiving node in metres? ', check_float))

    number_of_objects = int(checker('How many objects between the two nodes? ', check_int))

    objects = []
    largest_object = (0.0, 0.0)

    for i in range(1, number_of_objects+1):
        d = float(checker('Distance between object ' + str(i) + ' and the transmitting node in km?', check_float))
        h = float(checker('Height of object ' + str(i) + ' in metres?', check_float))
        objects.append((d, h))

        if h > largest_object[1]:
            largest_object = objects[-1]

    objects.sort()

    # Step 2: calculate height and distance of final object
    for i in range(len(objects)):
        for x in range(i+1, len(objects)):
            obj = calculate_effective_object(objects[i], objects[x], distance)
            if obj[1] > largest_object[1]:
                largest_object = obj

    d1 = largest_object[0]
    d2 = distance - d1
    h = largest_object[1]

    # Step 3: adjust height of final objects for earth curvature correction
    height_correction = d1 * d2 / 12.74 / 1.33
    h += height_correction

    # Step 4: calculate height of LOS over the object
    if hr > ht:
        los = (hr - ht) * d1 / distance + ht
    elif ht > hr:
        los = (ht - hr) * d2 / distance + hr
    else:
        los = ht

    # Step 5: calculate height of 0.6 first fresnel zone
    radius = 0.6 * 548 * (d1 * d2 / freq / distance) ** 0.5
    ffz_height = los - radius

    # Step 6: find the relevant case and calculate EPL
    if h < ffz_height:  # case 1/2
        pass
    elif h > los:  # case 4
        pass
    else:  # case 3
        pass

    print("EPL =",  epl)

    # Step 7: calculate APL
    apl = 0
    print("APL =",  apl)

    # Step 8: calculate FM
    fm = apl - epl
    print("FM =", fm)

    # Step 9: conclude if comms is through
    if fm > 20:
        print("Comms through!!!")


if __name__ == '__main__':
    main()
