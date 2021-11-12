#!/usr/bin/env python3
import random
import time
import sys

from pprint import pprint
from clize import run

INSERT=1
REMOVE=2
CHANGE=3

def comp_edit_dist(a, ac, b, bc, mat):
    if ac == len(a) and bc == len(b):
        # at end
        return 0

    # look up in mat
    v = mat[ac][bc]
    if v != -1:
        return v
    
    # calculate value for matrix
    elif (len(a) - ac) == 0:
        # just inserts left
        for x in range(bc, len(b)):
            dist = len(b) - x
            mat[ac][x] = dist
        return mat[ac][bc]
    
    elif (len(b) - bc) == 0:
        # just removals left
        for x in range(ac, len(a)):
            dist = len(a) - x
            mat[x][bc] = dist
        return mat[ac][bc]

    elif a[ac] == b[bc]:    
        # letters in pos match, continue
        return comp_edit_dist(a, ac+1, b, bc+1, mat)
    else:
        # try everything
        # look up distances in matrix by aind, bind
        s_ins = comp_edit_dist(a, ac, b, bc+1, mat)
        s_del = comp_edit_dist(a, ac+1, b, bc, mat)
        s_mut = comp_edit_dist(a, ac+1, b, bc+1, mat)

        ms = min((s_ins, s_del, s_mut))
        ms += 1
        mat[ac][bc] = ms
        return ms

def comp_edit_tree(a, ac, ao, b, bc, mat, depth):

    if (ac-ao) == len(a) and bc == len(b):
        # at end
        return (0, [])

    elif len(a[ac-ao:]) == 0:
        # just inserts left
        moves = [(INSERT, ac + x - bc, x) for x in range(bc, len(b))]
        return (len(moves), moves)
    
    elif len(b[bc:]) == 0:
        # just removals left
        moves = [(REMOVE, ac) for x in range(ac, len(a)+ao)]
        return (len(moves), moves)

    elif a[ac-ao] == b[bc]:    
        # letters in pos match, continue
        return comp_edit_tree(a, ac+1, ao, b, bc+1, mat, depth+1)
    else:
        # try everything
        # look up distances in matrix by aind, bind

        s_ins = comp_edit_dist(a, ac-ao, b, bc+1, mat)
        s_del = comp_edit_dist(a, ac+1-ao, b, bc, mat)
        s_mut = comp_edit_dist(a, ac+1-ao, b, bc+1, mat)

        ms = min((s_ins, s_del, s_mut))
        choice = []
        if s_del == ms:
            choice.append(REMOVE)
        if s_mut == ms:
            choice.append(CHANGE)
        if s_ins == ms:
            choice.append(INSERT)

        # choose a random one that is one of the shortest paths to follow
        sel = random.choice(choice)

        res = None

        if sel == REMOVE:
            sc_del, m_del = comp_edit_tree(a, ac, ao-1, b, bc, mat, depth+1)
            if sc_del != s_del:
                raise Exception("dist mismatch")
            res = [(REMOVE, ac)] + m_del

        elif sel == CHANGE:
            sc_mut, m_mut = comp_edit_tree(a, ac+1, ao, b, bc+1, mat, depth+1)
            if sc_mut != s_mut:
                raise Exception("dist mismatch")
            res = [(CHANGE, ac, bc)] + m_mut

        elif sel == INSERT:
            sc_ins, m_ins = comp_edit_tree(a, ac+1, ao+1, b, bc+1, mat, depth+1)
            if sc_ins != s_ins:
                raise Exception("dist mismatch")
            res = [(INSERT, ac, bc)] + m_ins

        ms += 1
        return (ms, res)

def print_matrix(a, b, mat):
    print("Matrix:")
    print(" "+ ''.join([' '+ x +' ' for x in b]))
    for i in range(len(a)+1):
        c = a[i] if i < len(a) else ' '
        print(c +' '+ ' '.join([str(x).zfill(2) for x in mat[i]]))
    print()

def randomize_path(a, b, path):
    # each edit is based on the string at that point
    # but should be able to be done at any point
    # (we wont remove what we add, etc)

    # order every character over time?
    # delete doesn't remove from array, just disables
    # insert doesn't add to array, just enables

    arr = []
    for i in range(len(a)):
        # aindex, bindex, enabled, opindex
        arr.append([i, -1, True, -1])

    for opi in range(len(path)):
        c = path[opi]
        if   c[0] == INSERT:
            aind = c[1]
            bind = c[2]

            # insert into arr
            # first find where aind is
            i = 0
            ai = 0
            while ai < aind:
                if arr[i][2]:
                    ai += 1
                i += 1
            arr.insert(i, [-1, bind, True, opi])
        elif c[0] == REMOVE:
            aind = c[1]

            # first find where aind is
            i = 0
            ai = 0
            while ai <= aind:
                if arr[i][2]:
                    ai += 1
                i += 1
            
            arr[i-1][2] = False # disable
            arr[i-1][3] = opi
        elif c[0] == CHANGE:
            aind = c[1]
            bind = c[2]

            # first find where aind is
            i = 0
            ai = 0
            while ai <= aind:
                if arr[i][2]:
                    ai += 1
                i += 1
            
            arr[i-1][1] = bind # apply bindex
            arr[i-1][3] = opi


    # check ourselves
    out = ""
    for i in range(len(arr)):
        c = arr[i]
        #print(i,"\t", c, "\t", a[c[0]] if c[0] != -1 else "_", b[c[1]] if c[1] != -1 else "_")
        if c[2]:
            if c[1] != -1:
                out += b[c[1]]
            else:
                out += a[c[0]]

    if out != b:
        raise Exception("Array doesn't match for randomization")

    # convert changes to stateless
    stateless = []
    for i in range(len(arr)):
        c = arr[i]
        if c[3] == -1:
            continue # this letter is untouched
        op = path[c[3]]
        # translate ai to stateless
        newop = (op[0], i) + op[2:]
        stateless.append(newop)

    # randomize stateless changes
    random.shuffle(stateless)

    # reset enabled
    for i in range(len(arr)):
        if arr[i][0] != -1:
            arr[i][2] = True
        else:
            arr[i][2] = False

    # convert changes back to stateful
    newpath = []

    for opi in range(len(stateless)):
        op = stateless[opi]

        # translate with what's enabled
        i = 0
        ai = 0
        while i < op[1]:
            if arr[i][2]:
                ai += 1
            i += 1

        newop = (op[0], ai) + op[2:]
        newpath.append(newop)

        # update enabled
        if   op[0] == INSERT:
            arr[op[1]][2] = True
        elif op[0] == REMOVE:
            arr[op[1]][2] = False
        elif op[0] == CHANGE:
            pass # noop for enable/disable

    #pprint(path)
    #pprint(stateless)
    #pprint(newpath)

    return newpath

def get_edits(a, b, sweep=False):

    # allocate matrix
    mat = []
    for i in range(len(a)+1):
        mat.append([-1]*(len(b)+1))

    # get path
    score, path = comp_edit_tree(a, 0, 0, b, 0, mat, 0)

    #print_matrix(a,b,mat)

    if not sweep:
        # randomize order
        path = randomize_path(a, b, path)

    # expand
    lines = [a]
    for c in path:
        n = lines[-1]
        if   c[0] == INSERT:
            aind = c[1]
            bind = c[2]
            n = n[:aind] + b[bind] + n[aind:]
        elif c[0] == REMOVE:
            aind = c[1]
            n = n[:aind] + n[aind+1:]
        elif c[0] == CHANGE:
            aind = c[1]
            bind = c[2]
            n = n[:aind] + b[bind] + n[aind+1:] 
        lines.append(n)
    return lines

def main(*, leadin=True, infile:'f'=None, inplace:'i'=True, linetime=0.06, staytime=0.45, seed=None, sweep=False):
    """Changes a character at a time between lines for a fun text transition effect

    :param infile: File path for input, otherwise stdin is used
    :param inplace: Use control codes to mutate the lines in place
    :param leadin: Start transition from nothing, as opposed to from the first line
    :param linetime: Time to display each transition state (requires inline)
    :param staytime: Time to display each output line (requires inline)
    :param seed: Seed for randomization
    :param sweep: If true mutations will move from left to right
    """
    # expects input on stdin, newline delimited
    # can output using one line, or as multiple lines

    if seed is None:
        seed = time.time()
    random.seed(seed)

    f = sys.stdin
    if infile is not None:
        f = open(infile, "r")

    if inplace:
        print()

        restore = "\x1b[1F\x1b[2K"
        istty = False

        # check if stdin is a tty
        if f.isatty():
            # record cursor
            istty = True

    lastline = ""
    if not leadin:
        lastline = f.readline()[:-1]

    while True:
        line = f.readline()
        if len(line) == 0:
            break

        if inplace and istty:
            # clear typed stuff
            print(restore, end="")
        
        # remove newline
        line = line[:-1]

        start = time.time()
        changes = get_edits(lastline, line, sweep)

        # need to display longer?
        if inplace:
            delta = time.time() - start
            if delta < staytime:
                time.sleep(staytime - delta)

        for c in changes:
            if inplace:
                # clear printed data first
                # TODO handle multiline?
                print(restore, end="")
                pass

            print(c)
            if inplace:
                time.sleep(linetime)

        lastline = line        

if __name__ == '__main__':
    run(main)
