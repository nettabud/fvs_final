#Netta Budniski & Saggie Mishan

import subprocess
import time


#translate and analayse a game in xsb
def trans_game(str_b):
    lines = str_b.split('\n')
    game = [list(line.strip()) for line in lines if line.strip()]
    return game

# creats the SMV script for the game
def create_smv_file(game):
    n = len(game) #rows
    m = len(game[0]) #coloums

    print(f'm {m} n {n}')
    
    smv_file = f"MODULE main\n"
    smv_file += f"VAR\n"


    
    #sets a new format for the game
    for i in range(n):
        for j in range(m):
            if game[i][j] != '#':
                smv_file += f"    pos_({i},{j}) : 1..3;\n"  # 1: empty, 2: box, 3: keeper

    smv_file += f"    steps_counter : 0..60;\n"

    # set the initial states
    # 1: empty (floor or goal), 2: box (on goal or not), 3: keeper (on goal or not)

    smv_file += f"INIT\n"
    initial_list = []


    for i in range(n):
        for j in range(m):
            if game[i][j] == '_':
                initial_list.append(f"pos_{i},{j}) = 1")
            elif game[i][j] == '$':
                initial_list.append(f"pos_({i},{j}) = 2")
            elif game[i][j] == '@':
                initial_list.append(f"pos_({i},{j}) = 3")
            elif game[i][j] == '.':
                initial_list.append(f"pos_({i},{j}) = 1")
            elif game[i][j] == '*':
                initial_list.append(f"pos_({i},{j}) = 2")
            elif game[i][j] == '+':
                initial_list.append(f"pos_({i},{j}) = 3")

    
    smv_file += " & ".join(initial_list) 
    smv_file += f" & steps_counter = 0\n"

    # define the possible trans_list
    smv_file += f"TRANS\n"
    smv_file += f"   case\n"
    trans_list = []
    d_opt = [(-1, 0), (1, 0), (0, -1), (0, 1)] #the options for all the moves of the keeper

    #checls if the position is possible for general move
    def gen_pos(x, y):
        return 0 <= x < m and 0 <= y < n and game[y][x] != '#'
    
    #checks if the position is possible for the keeper
    def keeper_pos(x, y):
        return  0 <= x < m and 0 <= y < n and game[y][x] != '#' and game[y][x] != '$' and game[y][x] != '*'
    deafult_lst = []
    deafult_lst.append(f"       TRUE:\n")    
    for y in range(n):
        for x in range(m):

            if keeper_pos(x,y):

                for dx, dy in d_opt:
                    next_x, next_y = x + dx, y + dy
                    if gen_pos(next_x, next_y):
                        print(next_x, next_y)
                        # Player move
                        trans_list.append(f"    (steps_counter < 60 & pos_({y},{x}) = 3 & pos_({next_y},{next_x}) = 1):\n")
                        trans_list.append(f"       next(pos_({y},{x})) = 1 &\n       next(pos_({next_y},{next_x})) = 3 &\n       next(steps_counter) = steps_counter + 1 \n")
                        for i in range(n):
                            for j in range(m):
                                if not (i == y and j == x) and not (i == next_y and j == next_x) and gen_pos(j, i):
                                    trans_list.append(f"       & next(pos_({i},{j})) = pos_({i},{j}) \n")   
                        trans_list.append(';')
                        # Box push
                        if keeper_pos(x + 2 * dx, y + 2 * dy):
                            nnext_x, nnext_y = x + 2 * dx, y + 2 * dy
                            trans_list.append(f"    (steps_counter < 60 & pos_({y},{x}) = 3 & pos_({next_y},{next_x}) = 2 & pos_({nnext_y},{nnext_x}) = 1):\n")
                            trans_list.append(f"       (next(pos_({y},{x})) = 1 &\n       next(pos_({next_y},{next_x})) = 3 &\n       next(pos_({nnext_y},{nnext_x})) = 2 &\n       next(steps_counter) = steps_counter + 1);\n") 
                           

            if gen_pos(x, y):
                deafult_lst.append(f"       (next(pos_({y},{x})) = pos_({y},{x}))&")

    deafult_lst.append(f"       (next(steps_counter) = steps_counter);")
    smv_file += "".join(trans_list) + "\n"
    smv_file += " \n ".join(deafult_lst) + "\n"
    smv_file += "   esac;\n"

    # set the LTL spec
    smv_file += f"LTLSPEC\n   ! (F ("
    goal_positions = [(i, j) for i in range(n) for j in range(m) if game[i][j] == '.']
    for idx, (i, j) in enumerate(goal_positions):
        if idx > 0:
            smv_file += " & "
        smv_file += f"(pos_({i},{j}) = 2)"
    smv_file += "));\n"

    return smv_file

#solve the game each time for ine box by making all the other box_positions walls
def iterative_soko(game_str):

    # Convert the game string to the game matrix representation
    game = trans_game(game_str)

    # Find all positions of boxes ('$' or '*') in the game
    box_positions = [(i, j) for i in range(len(game)) for j in range(len(game[0])) if game[i][j] in ['$', '*']]

    # Find all goal positions ('.', '*', or '+') in the game
    goal_positions = [(i, j) for i in range(len(game)) for j in range(len(game[0])) if game[i][j] in ['.', '*', '+']]

    # Set the maximum number of steps for the game; this limit can be adjusted as needed
    max_steps = 60

    # Initialize loop counter
    loop_number = 0

    # Record the initial time to measure total runtime
    initial_time = time.time()

    # Iterate through pairs of box positions and goal positions
    for box, goal in zip(box_positions, goal_positions):
        # Create the SMV file content for the current box and goal
        smv_file = create_smv_file(game)
        smv_name = "sokoban_temp.smv"
        
        # Write the SMV file content to a temporary file
        with open(smv_name, "w") as f:
            f.write(smv_file)

        # Record the time at the start of the loop iteration
        first_loop_time = time.time()
        
        # Run the SMV file and get the output file name
        outfile = smv_run(smv_name)
        
        # Record the time at the end of the loop iteration
        iteration_end_time = time.tcrime()
        
        # Increment the loop counter
        loop_number += 1

        # Read the output file content
        with open(outfile, "r") as f:
            output_str = f.read()

        # Check if the game configuration is winnable
        if "is true" in output_str:
            print(f" For loop number {loop_number}: the game with box at {box} to goal at {goal} isn't winnable")
        else:
            print(f"For loop number {loop_number}: the game with box at {box} to goal at {goal} - is winnable!")

        # Print the runtime for the current loop iteration
        print(f"For loop number {loop_number} the runtime is: {iteration_end_time - first_loop_time:.2f} seconds")

        # Record the total end time
        end_time = time.time()

        # Print the number of loops executed
        print(f"number of loops: {loop_number}")

        # Print the total runtime for all iterations
        print(f"Total Runtime: {end_time - initial_time:.2f} seconds")

#run smv file
def smv_run(smv_name):
    nuxmv_process = subprocess.Popen(["nuXmv", smv_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    outfile = smv_name.split(".")[0] + ".out"

    stdout, _ = nuxmv_process.communicate()

    # Save output to file
    with open(outfile, "w") as f:
        f.write(stdout)
    print(f"Output saved to {outfile}")

    return outfile

#winnable
game = """\
#####
#$@.#
#####
"""

#winnable
'''
game = """\
#######
###.###
###$###
#.$@$.#
###$###
###.###
#######
"""
'''



# Solve Sokoban game iteratively
iterative_soko(game)
