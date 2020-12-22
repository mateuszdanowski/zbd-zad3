import sys
import psycopg2
import random

CANDIES = ('Czekolada Studencka', 'Kasztanki', 'Milka', 'Kinder niespodzianka', 'Toffifee')
MAX_CANDIES = 5


def append_to_file(elf_no, letter_no, letter_info):
    filename = f'dataset/elf{elf_no}'

    # Arbitrary values, probably want to randomize them
    letter_len = random.randint(1, MAX_CANDIES)
    chosen_candies = random.sample(CANDIES, letter_len)
    # country = 'Polska'
    # recipient_desc = 'Krzysztof Ciebiera'

    # candy_name = 'Czekolada'
    # quantity = 65

    with open(filename, 'a') as file:
        country, recipient_desc = letter_info

        # Write a header
        file.write(f'{letter_len};{country};{recipient_desc}\n')

        # Write a list of candies
        for i in range(letter_len):
            candy_name = chosen_candies[i]
            quantity = random.randint(1, MAX_CANDIES)

            file.write(f'{candy_name};{quantity}\n')


def write_file(file_index, N):
    filename = f'dataset/elf{file_index}'
    with open(filename, 'w') as file:
        file.write(f'{N}\n')


def generate_dataset(n_sets, n_letters):
    print('Generating dataset for elfs...')

    letters_info = [('Polska', 'Krzysztof Ciebiera'), ('Niemcy', 'Lukas Zimmerman'), ('Hiszpania', 'Miguel Rodriguez'), ('Włochy', 'Luigi Bernolli'), ('USA', 'Donald Trump')]

    for elf_no in range(1, n_sets + 1):
        # Write the number of letters
        write_file(elf_no, n_letters)
        for letter_no in range(n_letters):
            letter_info = letters_info[letter_no % len(letters_info)]

            # Write the letters
            append_to_file(elf_no, letter_no, letter_info)

    print('OK')


def generate_data_for_candies_in_stock(candies):
    # quantities = (1, 10, 100, 1000, 10000)
    quantities = (1000, 1000, 1000, 1000, 1000)
    # quantities = (10000, 10000, 10000, 10000, 10000)

    candies_in_stock = zip(candies, quantities)

    return candies_in_stock


def generate_data_for_similar_candies(candies):
    similarity_levels = (0.9, 0.25, 0.5, 0.1, 0.99, 0.45, 0.5, 0.4, 0.2, 0.1, 0.6, 0.2, 0.9, 0.25, 0.5, 0.1, 0.99, 0.45, 0.5, 0.4)

    similar_candies = []

    i = 0
    for candie1 in candies:
        for candie2 in candies:
            if candie1 != candie2:
                similar_candies.append((candie1, candie2, similarity_levels[i]))
                i += 1

    return similar_candies


def insert_into_candies_in_stock(cur, candies):
    candies_in_stock = generate_data_for_candies_in_stock(candies)

    for candie_in_stock in candies_in_stock:
        cur.execute("INSERT INTO candies_in_stock VALUES (%s, %s);", candie_in_stock)


def insert_into_similar_candies(cur, candies):
    similar_candies = generate_data_for_similar_candies(candies)

    for similar_candy in similar_candies:
        cur.execute("INSERT INTO similar_candies VALUES (%s, %s, %s);", similar_candy)


def insert_tables():
    print('Inserting data into tables...')

    conn = psycopg2.connect("dbname=mateuszdanowski")
    cur = conn.cursor()

    candies = ('Czekolada Studencka', 'Kasztanki', 'Milka', 'Kinder niespodzianka', 'Toffifee')
    insert_into_candies_in_stock(cur, candies)
    insert_into_similar_candies(cur, candies)
    conn.commit()

    cur.close()
    conn.close()

    print('OK')


if __name__ == '__main__':
    n_sets = 20
    n_letters = 100

    for i in range(1, len(sys.argv)):
        split_equal = sys.argv[i].split('=')
        if len(split_equal) != 2:
            continue
        
        name = split_equal[0]
        value = int(split_equal[1])
        
        if name == "sets":
            n_sets = value
        elif name == "letters":
            n_letters = value
        else:
            continue


    # Generate N sets of M letters (all equal?)
    generate_dataset(n_sets, n_letters)

    insert_tables()
