from random import randrange, choice

# Entity info (DNA):
# 00-24: Health (100)
# 25-27: Speed (12)
# 28-30: Strength (12)
# 31-35: Size (20)
# 36-50: Radius (60)


def gamble(chance):
    a = randrange(100)
    if a <= 100*chance:
        return 1
    return 0


def stats(dna):
    if len(dna) >= 46:
        return {
            'health': sum(dna[:25]),
            'speed': sum(dna[25:28]),
            'strength': sum(dna[28:31]),
            'size': sum(dna[31:36]),
            'radius': sum(dna[36:51])
        }


def generate(parent, mutation=0.2):
    parent = parent.dna
    child = []

    for p in parent:
        val = p

        if gamble(mutation):
            val = choice([x for x in [1, 2, 3, 4] if x != val])

        child.append(val)
    return child


def rand():
    dna = []
    for _ in range(51):
        dna.append(choice([1, 2, 3, 4]))
    return dna
