#Netta Budniski & Saggie Mishan

import subprocess
import time

# Translate and analyze a game in xsb
def trans_game(str_b):
    lines = str_b.split('\n')
    game = [list(line.strip()) for line in lines if line.strip()]
    return game

# Creates the SMV script for the game
def create_smv_file(game):
    n = len(game)  # rows
    m = len(game[0])  # columns

    smv_file = f"MODULE main\n"
    smv_file += f"VAR\n"

    # Sets a new format for the game
    for i in range(n):
        for j in range(m):
            if game[i][j] != '#':
                smv_file += f"    pos_{i}{j} : 1..3;\n"  # 1: empty, 2: box, 3: keeper

    smv_file += f"    steps_counter : 0..60;\n"

    # Set the initial states
    smv_file += f"INIT\n"
    initial_list = []

    for i in range(n):
        for j in range(m):
            if game[i][j] == '_':
                initial_list.append(f"pos_{i}{j} = 1")
            elif game[i][j] == '$':
                initial_list.append(f"pos_{i}{j} = 2")
            elif game[i][j] == '@':
                initial_list.append(f"pos_{i}{j} = 3")
            elif game[i][j] == '.':
                initial_list.append(f"pos_{i}{j} = 1")
            elif game[i][j] == '*':
                initial_list.append(f"pos_{i}{j} = 2")
            elif game[i][j] == '+':
                initial_list.append(f"pos_{i}{j} = 3")

    smv_file += " & ".join(initial_list)
    smv_file += f" & steps_counter = 0\n"

    # Define the possible trans_list
    smv_file += f"TRANS\n"
    smv_file += f"   case\n"
    trans_list = []
    d_opt = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # the options for all the moves of the keeper

    # Checks if the position is possible for a general move
    def gen_pos(x, y):
        return 0 <= x < m and 0 <= y < n and game[y][x] != '#'

    # Checks if the position is possible for the keeper
    def keeper_pos(x, y):
        return 0 <= x < m and 0 <= y < n and game[y][x] != '#' and game[y][x] != '$' and game[y][x] != '*'

    deafult_lst = []
    deafult_lst.append(f"       TRUE:\n")
    for y in range(n):
        for x in range(m):
            if keeper_pos(x, y):
                for dx, dy in d_opt:
                    next_x, next_y = x + dx, y + dy
                    if gen_pos(next_x, next_y):
                        # Player move
                        trans_list.append(f"    (steps_counter < 60 & pos_{y}{x} = 3 & pos_{next_y}{next_x} = 1):\n")
                        trans_list.append(f"       next(pos_{y}{x}) = 1 &\n       next(pos_{next_y}{next_x}) = 3 &\n       next(steps_counter) = steps_counter + 1 \n")
                        for i in range(n):
                            for j in range(m):
                                if not (i == y and j == x) and not (i == next_y and j == next_x) and gen_pos(j, i):
                                    trans_list.append(f"       & next(pos_{i}{j}) = pos_{i}{j} \n")
                        trans_list.append(';')
                        # Box push
                        if keeper_pos(x + 2 * dx, y + 2 * dy):
                            nnext_x, nnext_y = x + 2 * dx, y + 2 * dy
                            trans_list.append(f"    (steps_counter < 60 & pos_{y}{x} = 3 & pos_{next_y}{next_x} = 2 & pos_{nnext_y}{nnext_x} = 1):\n")
                            trans_list.append(f"       (next(pos_{y}{x}) = 1 &\n       next(pos_{next_y}{next_x}) = 3 &\n       next(pos_{nnext_y}{nnext_x}) = 2 &\n       next(steps_counter) = steps_counter + 1);\n")

            if gen_pos(x, y):
                deafult_lst.append(f"       (next(pos_{y}{x}) = pos_{y}{x})&")

    deafult_lst.append(f"       (next(steps_counter) = steps_counter);")
    smv_file += "".join(trans_list) + "\n"
    smv_file += " \n ".join(deafult_lst) + "\n"
    smv_file += "   esac;\n"

    # Set the LTL spec
    smv_file += f"LTLSPEC\n   ! (F ("
    goal_positions = [(i, j) for i in range(n) for j in range(m) if game[i][j] == '.']
    for idx, (i, j) in enumerate(goal_positions):
        if idx > 0:
            smv_file += " & "
        smv_file += f"(pos_{i}{j} = 2)"
    smv_file += "));\n"

    return smv_file

def solve_sokoban(board_str):
    board = trans_game(board_str)
    smv_model = create_smv_file(board)

    # Write SMV model to a temporary file
    model_filename = "sokoban2.smv"
    with open(model_filename, "w") as f:
        f.write(smv_model)

    # Read and print the content of the SMV file
    with open(model_filename, 'r') as file:
        content = file.read()
        print(content)

    # Run nuXmv to check for winning condition
    output_filename = smv_run(model_filename)

    # Parse nuXmv output to check if winnable and extract solution
    with open(output_filename, "r") as f:
        output_str = f.read()

    if "is true" in output_str:
        print("Board is not winnable!")
        # Extract and print winning solution (LURD format)
        # Add solution extraction logic here based on nuXmv_output
    else:
        print("Board is winnable.")

# Run smv file
def smv_run(smv_name):
    nuxmv_process = subprocess.Popen(["nuXmv", smv_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    outfile = smv_name.split(".")[0] + ".out"

    stdout, _ = nuxmv_process.communicate()

    # Save output to file
    with open(outfile, "w") as f:
        f.write(stdout)
    print(f"Output saved to {outfile}")

    return outfile

# Example Sokoban game in XSB format
# Winnable game
game = """\
#####
#@$.#
#####
"""

# Solve Sokoban game iteratively
solve_sokoban(game)
