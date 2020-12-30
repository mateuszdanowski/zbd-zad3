import sys
import psycopg2
import time

ELF_NO = "00"

DEBUG = False

def print_stats(elf_no, transactions, commited, finish_time):
    full = False

    if transactions > 0:
        print(f'\nElf number {elf_no} has done {transactions} transactions.\n{commited} ended in COMMIT, {transactions - commited} ended in ROLLBACK.\nThat is {round(commited / transactions * 100, 2)}% success rate\n')
    else:
        print(f"\nElf number {elf_no} hasn't done any transactions :o\n")

    with open("elfs-results", "a") as output:

        if full:
            if (int(elf_no) < 10):
                elf_no = f'0{str(elf_no)}'

            if transactions > 0:
                output.write(f'{elf_no}: {commited}/{transactions} ({round(commited / transactions * 100, 2)}%)\n')
            else:
                output.write(f'{elf_no}: {commited}/{transactions}\n')
        else:
            output.write(f'{elf_no};{int(commited / transactions * 100)};{finish_time}\n')


# 1 letter -> 1 package
# Create package based on the letter
def create_package(cur, letter_info, letter_content):

    # 1. Get package info (country, recipient_desc)
    country, recipient_desc = letter_info

    # Optimization
    letter_content = sorted(letter_content)

    # Optimization?? (if set to True)
    update_on_finish = False

    # 2. Add package to the table 'packages'
    cur.execute("INSERT INTO packages VALUES (DEFAULT, %s, %s) RETURNING id;", [country, recipient_desc])
    package_id = cur.fetchall()[0][0]
   
    if DEBUG:
        print(f'{ELF_NO}: Package id for {country}, {recipient_desc}: {package_id}') # debug

    # 3. Itarate over candies in the list
    for candy_name, wanted_quantity in letter_content:
        if DEBUG:
            print(f'{ELF_NO}: Next pos in letter: {candy_name}, {wanted_quantity}') # debug

        cur.execute("SELECT in_stock FROM candies_in_stock WHERE name = %s;", [candy_name])
        query_result = cur.fetchall()

        # Error handle
        if len(query_result) == 0:
            if DEBUG:
                print(f'{ELF_NO}: ERROR: no candy name as {candy_name}')
            return False
        if len(query_result) > 1:
            if DEBUG:
                print(f'{ELF_NO}: ERROR: there are multiple candies named {candy_name}')
            return False

        in_stock = query_result[0][0]
        if DEBUG:
            print(f'{ELF_NO}: How many in stock:', in_stock) # debug

        chosen_candy = candy_name

        # Check if there is enough candy
        if in_stock < wanted_quantity:
            chosen_candy = None

            # Find similar candies
            cur.execute("SELECT similar_to FROM similar_candies WHERE candy = %s ORDER BY similarity_level DESC;", [candy_name])
            query_result = cur.fetchall()

            # Nasty adversary elf
            # if elf_no == 10:
            #     print("SLEEP")
            #     time.sleep(0.5)

            if len(query_result) < 1:
                if DEBUG:
                    print(f"{ELF_NO}: Not enough in stock, no similar candies, can't meet the criteria :(")
                return False

            similar_candies = []
            for result in query_result:
                similar_candies.append(result[0])

            if DEBUG:
                print(f'{ELF_NO}: Not enough in stock, similar candies: {similar_candies}') # debug

            # Find first one that can be used
            for similar_candie in similar_candies:
                cur.execute("SELECT in_stock FROM candies_in_stock WHERE name = %s;", [similar_candie])
                in_stock = cur.fetchall()[0][0]

                # Nasty adversary elf
                # if elf_no == 10:
                #     print("SLEEP")
                #     time.sleep(0.5)

                if DEBUG:
                    print(f'{ELF_NO}: Similar candy: {similar_candie}, in stock: {in_stock}')
                if in_stock >= wanted_quantity:
                    if DEBUG:
                        print(f'{ELF_NO}: It can be used!') # debug
                    chosen_candy = similar_candie;
                    break

        if DEBUG:
            print(f'{ELF_NO}: Chosen candy: {chosen_candy}') # debug

        if chosen_candy is None:
            print("NO CANDIES FOUND :(")
            return False

        # debug ## CHECK
        # cur.execute("SELECT * FROM candies_in_package;")
        # print(f'SELECT * FROM candies_in_package: {cur.fetchall()}')

        # Add chosen_candy to the package
        cur.execute("INSERT INTO candies_in_package VALUES (%s, %s, %s);", [package_id, chosen_candy, wanted_quantity])

        if not update_on_finish:
            try:
                cur.execute("UPDATE candies_in_stock SET in_stock = in_stock - %s WHERE name = %s;", [wanted_quantity, chosen_candy])
                
                # Nasty adversary elf
                # if elf_no == 10:
                #     print("SLEEP")
                #     time.sleep(0.5)
            except Exception as error:
                print(f'{ELF_NO}: ERROR: Update failed (in_stock constraint): {error}')
                return False

    if update_on_finish:
        cur.execute("SELECT candy_name, quantity FROM candies_in_package WHERE package_id = %s", [package_id])
        candies_in_package = cur.fetchall()

        try:
            for chosen_candy, wanted_quantity in candies_in_package:
                cur.execute("UPDATE candies_in_stock SET in_stock = in_stock - %s WHERE name = %s;", [wanted_quantity, chosen_candy])
        except Exception as error:
            print(f'{ELF_NO}: ERROR: (update on finish) Update failed (in_stock constraint): {error}')
            return False

    # 4. Success if all criteria were met
    return True


def simulate_elf(elf_no):
    transactions = 0
    commited = 0

    letters_for_elf = f"./dataset/elf{elf_no}";

    conn = psycopg2.connect("dbname=mateuszdanowski")
    cur = conn.cursor()

    # Optimalization
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)

    start_time = time.time()
    try:
        with open(letters_for_elf, 'r') as letters_file:
            N = int(letters_file.readline().strip())
            if DEBUG:
                print(f'{ELF_NO}: N = {N}') # debug

            for package_no in range(1, N + 1):
                if DEBUG:
                    print(f'{ELF_NO}: Letter number: {package_no}') # debug

                letter_len, country, recipient_desc = letters_file.readline().strip().split(';')
                if DEBUG:
                    print(f'{ELF_NO}: Letter info: {letter_len}, {country}, {recipient_desc}') # debug
                letter_info = (country, recipient_desc)

                letter_content = []
                for pos_in_letter in range(1, int(letter_len) + 1):
                    candy_name, quantity = letters_file.readline().strip().split(';')
                    if DEBUG:
                        print(f'{ELF_NO}: Next on the list ({pos_in_letter}): {candy_name}, {quantity}') # debug
                    
                    letter_content.append((candy_name, int(quantity)))

                if DEBUG:
                    print(f'{ELF_NO}: BEGIN') # debug

                transactions += 1

                # Uncomment if working in read_committed
                # package_created = create_package(cur, letter_info, letter_content)

                # Optimalization
                # Comment out if working in serializable
                package_created = False
                retry_no = 0
                while retry_no < 10000:
                    try:
                        package_created = create_package(cur, letter_info, letter_content)
                    except Exception as error:
                        retry_no += 1
                        if DEBUG:
                            print(f'{ELF_NO}: Error during packing, retry number {retry_no}: {error}')
                    if package_created:
                        break


                # Commit or Rollback depending on the result
                if package_created:
                    if DEBUG:
                        print(f'{ELF_NO}: COMMIT') # debug
                    commited += 1
                    conn.commit()
                else:
                    if DEBUG:
                        print(f'{ELF_NO}: ROLLBACK') # debug
                    conn.rollback()

    except IOError:
        print(f'{ELF_NO}: ERROR: file for elf number {elf_no} not found :(')

    cur.close()
    conn.close()

    end_time = time.time()
    print_stats(elf_no, transactions, commited, end_time - start_time)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Provide number as an argument!")
        exit(0)
    
    elf_no = int(sys.argv[1])

    ELF_NO = str(elf_no) if elf_no > 9 else f'0{str(elf_no)}'

    simulate_elf(elf_no)