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


    
    #sets a new format for the board
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
                initial_list.append(f"pos_({i},{j}) = 1")
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
    goals = [(i, j) for i in range(n) for j in range(m) if game[i][j] == '.']
    for idx, (i, j) in enumerate(goals):
        if idx > 0:
            smv_file += " & "
        smv_file += f"(pos_({i},{j}) = 2)"
    smv_file += "));\n"

    return smv_file

# Run the smv and tell if it's winnabl or not
def solve_sokoban(str_b):
    game = trans_game(str_b)
    smv_file = create_smv_file(game)

    # create a new snv file
    smv_name = "sokoban2.smv"
    with open(smv_name, "w") as f:
        f.write(smv_file)

    # run the smv to see the result
    outfile = smv_run(smv_name)

    #read the smv to see if it's possible to win 
    with open(outfile, "r") as f:
        result = f.read()

    if "is true" in result:
        print("You can't win the game!")
    else:
        print("You can win the game, good luck :)")

#run smv file
def smv_run(smv_name, engine):
    initial_time = time.time()
    
    #run subproccess of the nuxmv on bdd/sat each time
    nuxmv_process = subprocess.Popen(
        ["nuXmv", "-int"], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        universal_newlines=True
    )
    
    #run in the nuxmv:
    smv_ins = f"set {engine}\nread_model {smv_name}\ngo\ncheck_ltlspec\nquit\n"
    
    # Send smv_ins to nuXmv and get the output
    stdout, stderr = nuxmv_process.communicate(smv_ins)
    
    end_time = time.time()
    tot_time = end_time - initial_time

# Save the output to a file
    outfile = smv_name.split(".")[0] + f"_{engine}.out"
    with open(outfile, "w") as f:
        f.write(stdout)
    
    print(f"Output is in the file: {outfile}")
    print(f"Time: {engine.upper()} engine: {tot_time:.2f} seconds")
    
    return tot_time

# measure bdd and sat perfomrmmance
def measure_performance(board_str):
    board = trans_game(board_str)
    smv_file = create_smv_file(board)

    #write smv file
    smv_name = "sokoban.smv"
    with open(smv_name, "w") as f:
        f.write(smv_file)

    #run with engines
    bdd_pref = smv_run(smv_name, "bdd")
    sat_pref = smv_run(smv_name, "sat")

    # Compare the two engines
    print(f"\nPerformance Comparison:")
    print(f"BDD Engine: {bdd_pref:.2f} seconds")
    print(f"SAT Engine: {sat_pref:.2f} seconds")
    if bdd_pref < sat_pref:
        print("BDD has better performences.")
    else:
        print("SAT has better performences.")

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

#not winnable

'''
game = """\
########
#@__$$##
########
#___..##
########
"""
'''

# Measure performance of nuXmv’s BDD and SAT Solver engines
measure_performance(game)