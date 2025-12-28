#!/usr/bin/python3
# import subprocess
import os

rootdir = 'Program/'
outdir = 'program_c/'  

for home, dirs, files in os.walk(rootdir):
    relpath = os.path.relpath(home, rootdir)
    outsub = os.path.join(outdir, relpath)
    os.makedirs(outsub, exist_ok=True)

    for filename in files:
        # print(os.path.join(home, filename))
        if filename.endswith('.txt'):
            c_file = filename[:-4]+".c"
            # cc_file = filename[:-4] + ".cc"
            inpath = os.path.join(home, filename)
            outpath = os.path.join(outsub, c_file)

            f = open(inpath, "r", errors="ignore")
            cf = open(outpath, "w")
            # ccf = open(os.path.join(home, cc_file), "w")

            cf.write("#include <stdio.h>\n#include <string.h>\n#include <math.h>\n#include <stdlib.h>\n#include <limits.h>\n#include <stdbool.h>\n\n")
            # ccf.write("#include <cstdio>\n#include <cstring>\n#include <cmath>\n#include <cstdlib>\n#include <iostream>\nusing namespace std;\n\n")

            code = f.read()
            code = code.replace("void main", "int main")
            code = code.replace("double main", "int main")
            code = code.replace("char main", "int main")
            code = code.replace("main()", "int main()")
            code = code.replace("int int main()", "int main()")

            cf.write(code)
            # ccf.write(code)
            f.close()
            cf.close()
            # ccf.close()
