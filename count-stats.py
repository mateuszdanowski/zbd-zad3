

def count_stats():
    with open('elfs-results', 'r') as results:
        sum_percent = 0
        sum_finish_time = 0
        n_lines = 0
        for line in results.readlines():
            percent, finish_time = line.split(';')
            sum_percent += int(percent)
            sum_finish_time += float(finish_time)
            n_lines += 1

        avg_percent = round(sum_percent / n_lines, 2)
        avg_time = round(sum_finish_time / n_lines, 2)
        print(f'Average percent of succesfull transactions: {avg_percent}%')
        print(f"Average time of elf's work: {avg_time}s")

if __name__ == '__main__':
    count_stats()