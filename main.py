from math import log10


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
    # radio = int(checker('Radio type (406/408): ', lambda r: r in ['406', '408']))
    # freq = float(checker('Transmitting frequency: ', lambda f: check_freq(radio, f)))
    # distance = float(checker('Total distance between the nodes (km): ', check_float))
    # ht = float(checker('Height of transmitting node (m): ', check_float))
    # hr = float(checker('Height of receiving node (m): ', check_float))

    radio = 406
    freq = 610
    distance = 10
    ht = 30
    hr = 30

    number_of_objects = int(checker('\nNumber of objects between the two nodes: ', check_int))

    objects = []
    largest_object = (0.0, 0.0)

    for i in range(1, number_of_objects+1):
        d = float(checker('\nDistance between object ' + str(i) + ' and transmitting node (km): ',
                          lambda dist: check_float and float(dist) < distance))
        h = float(checker('Height of object ' + str(i) + ' (m): ', check_float))
        objects.append((d, h))

        if h > largest_object[1]:
            largest_object = objects[-1]

    objects.sort()

    print ""

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
    height_correction = d1 * d2 / 12.75 / 0.7
    h += height_correction

    print "The final calculated object is " + str(d1) + \
          "km away from the transmitting node, with a height of " + str(h) + "m"

    # Step 4: calculate height of LOS over the object
    if hr > ht:
        los = (hr - ht) * d1 / distance + ht
    elif ht > hr:
        los = (ht - hr) * d2 / distance + hr
    else:
        los = ht

    print "The height of the LOS over the object is " + str(los) + "m"

    # Step 5: calculate height of 0.6 first fresnel zone
    radius = 0.6 * 548 * (d1 * d2 / freq / distance) ** 0.5
    ffz_height = los - radius

    print "0.6 of the first fresnel zone radius is " + str(radius) + "m"

    # Step 6: find the relevant case and calculate EPL
    fsl = 20 * log10(41.87 * freq * distance)
    pel = 115.11 + 40 * log10(distance) - 20 * log10(ht * hr)

    if h < ffz_height:  # case 1/2 no obstruction within 0.6 of the first fresnel zone
        epl = fsl
        print "Since the object is not within 0.6 of the first fresnel zone, EPL = FSL"
    elif h > los:  # case 4
        if fsl > pel:
            sl_fs = 19.22 * log10(h) - 9.5 * log10(d1) + 10 * log10(freq) - 41.84
            epl = fsl + sl_fs
        else:
            sl_pe = 20.3 * log10(h) - 20 * log10(d1) + 10 * log10(freq) - 40
            epl = pel + sl_pe
        print "Since the object blocks the LOS, EPL = FSL + SL"
    else:  # case 3
        epl = pel
        print "Since the object is within 0.6 of the first fresnel zone but does not block the LOS, EPL = PEL"

    print "\nEPL =",  epl

    # Step 7: calculate APL, we assume receiver sensitivity using 2048MBps
    if radio == 408:
        apl = 36. + 2 * 20 - 2 * 2.4 - (-82)
    else:
        apl = 40. + 2 * 15 - 2 * 9 - (-82)
    print "APL =",  apl

    # Step 8: calculate FM
    fm = apl - epl
    print "FM =", fm

    # Step 9: conclude if comms is through
    if fm > 20:
        print "\nComms through!!!"
    else:
        print "\nNo comms :("


if __name__ == '__main__':
    main()
