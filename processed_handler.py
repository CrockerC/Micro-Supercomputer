
def processed_handler(processed, node):
    try:
        disp = processed[node][-1], len(processed[node])
    except IndexError:
        disp = processed[node]
    print(*disp)
