#!/usr/bin/env python

# python3 status: compatible

# Stuff for taking 2d matrices and making tables for AFNI group
# analysis programs like 3dMVM, MBA, etc.
#
# In particular, these funcs are for interacting with 3dNetCorr and
# 3dTrackID outputs.

# --------------------------------------------------------------------------
auth = 'PA Taylor'
#
ver = '0.0' ; date = 'June 8, 2020'
# [PT] inputs
#
# --------------------------------------------------------------------------

import sys, os, copy, glob

from   afnipy import afni_base      as ab
from   afnipy import afni_util      as UTIL
from   afnipy import lib_mat2d_base as lm2b
from   afnipy import lib_csv        as LCSV

#cbar_link = 'https://scipy.github.io/old-wiki/pages'
#cbar_link+= '/Cookbook/Matplotlib/Show_colormaps'
cbar_link = 'https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html'

# ---------------------------------------------------------------------------

# defaults
ddefs = {
    'DEF_ver'               : ver,
    'DEF_date'              : date,
    'DEF_auth'              : auth,
}

# ----------------------------------------------------------------------------

help_string = '''
  PURPOSE ~1~

  This program is to make tables for AFNI group analysis programs from
  outputs from 3dNetCorr (*.netcc) and 3dTrackID (*.grid).

  This program can also include additional subject information from
  CSV files (which can be saved/made from spreadsheet formats like
  XLS, XLSX, etc.).

  Ver  : {DEF_ver}
  Date : {DEF_date}
  Auth : {DEF_auth}

------------------------------------------------------------------------------

INPUTS ~1~

  + A set of *.netcc or *.grid file output by 3dNetCorr or 3dTrackID,
    respectively.

  + (opt) a CSV file of subject data; note that 

------------------------------------------------------------------------------

OUTPUTS ~1~

  + a table file, usable in (many) AFNI group analysis programs

  + a log file reporting on the inputs, matching and other aspects of
    creating the table file

------------------------------------------------------------------------------

RUNNING ~1~

 -in_mat  IM1 IM2 IM3 ...
                :(req) name(s) of *.netcc or *.grid files with matrices
                 to be used to make table (probably more than one); the
                 list can be provided using wildcard chars, e.g.: 
                    group_dir/sub_*.grid 
                    sub_00?.netcc
                 (see also '-in_list ..' as an alternative method for 
                  inputting this information)

 -in_csv CSV    :(opt) name of a CSV file to include in table (just one).
                 The first column of the CSV must have subj ID labels
                 that can be matched with the filename/paths of the 
                 input matrix files.  If the subjects IDs cannot be 
                 unambiguously matched with the matrix files based on their
                 path/names, then you must use the '-in_list ..' option
                 to provide the matching explicitly

 -in_listfile LIST :(opt) another way of inputting the matrix (*.grid or
                 *.netcc) files-- by explicit path, matched per file
                 with a CSV subject ID.
                 The LIST text file contains two columns if also using 
                 a CSV:
                    col 1: path to subject matrix files
                    col 2: CSV IDs
                 Otherwise, if no CSV is being used, the file can contain
                 just one column of paths to the matrix files.
                 Note that lines in the LIST can contain #-ed comments.

 -prefix PP     :(req) output basename for the table and log files.  
                 Note that this can include path information, but both 
                 a suffix and a file extensions will be added for the
                 main outputs: 
                    _prep.log  (attached to the log file)
                    _tbl.txt   (attached to the table file)

 -pars PARS     :(opt) list of matrices to be included in the table, 
                 identified by their parameter name.  If no '-pars ..'  
                 list is provided, then all matrices in the input file 
                 will be included in the table (which might make for a 
                 veeery long table)


 ****



 -ver           :display current version
                 ({DEF_ver})

 -date          :display release/editing date of current version
                 ({DEF_date})

 -help          :display help (in terminal)
 -h             :display help (in terminal)

 -hview         :display help (in separate text editor)

------------------------------------------------------------------------------

EXAMPLES ~1~

 ****

'''.format(**ddefs)


# make list and dictionary of all opts, used below in parsing user inputs
opts_list = ab.parse_help_text_for_opts( help_string )
opts_dict  = {} 
for x in opts_list:
    opts_dict[x[1:]] = x

# ---------------------------------------------------------------------------

def read_in_listfile(fname, lines=1, strip=1, noblank=1, verb=1):
    """Read in a "listfile", which could have 1 or 2 columns.

    Return a list of the first column, and if the second column is
    given, the list of that; if there was only one column in the file,
    the second list is empty

    """
    
    L  = UTIL.read_text_file( fname, 
                              lines=lines, strip=strip,
                              noblank=noblank, verb=verb )
    L2 = [x.split() for x in L]
    
    
    nrow, ncolmin, ncolmax, is_rag, is_sq \
        = UTIL.mat_row_mincol_maxcol_ragged_square(L2)

    if is_rag :
        ab.EP("Cannot have a ragged listfile")

    if not([1, 2].__contains__(ncolmax)) :
        ab.EP("Need to 1 or 2 cols in listfile, not {}".format(ncolmax))

    col0 = [x[0] for x in L2]
    if ncolmax == 2 :         col1 = [x[1] for x in L2]
    else:                     col1 = []

    return col0, col1

# ---------------------------------------------------------------------------

class iopts_obj:
    """
    store all the argv-entered things opts to plot
    """

    def __init__( self ) :

        self.full_cmd         = None
        self.in_mat           = []      # will be globbed+sorted
        self.in_csv           = None
        self.in_listfile      = None
        self.pars_list        = [] 
        self.prefix           = None

    # ---------- check ----------------

    def check_req(self):
        ''' Check for and point out any missing inputs.'''
        MISS = 0

        if not(self.prefix) :
            ab.EP("missing '{prefix}' value"
                  "".format(**opts_dict), end_exit=False)
            MISS+=1

        if not(self.in_mat) and self.in_listfile==None :
            ab.EP("Must use at least one of '{in_mat}' or '{in_listfile}"
                  "".format(**opts_dict), end_exit=False)
            MISS+=1

        return MISS

    def finish_defs(self):
        """Check a couple things with input. 

        All input files/globs get parsed here.

        """

        if self.in_mat :
            # replace with actual list of files, because it might just
            # have been the glob list that was input
            self.in_mat = UTIL.list_files_by_glob(self.in_mat,
                                                  sort=True,
                                                  exit_on_miss=True)

        if self.in_csv :
            # replace with CSV file
            all_csv = UTIL.list_files_by_glob(self.in_csv,
                                              sort=True,
                                              exit_on_miss=True)
            if len(all_csv) > 1 :
                ab.EP("Too many files found when globbing with:\n"
                      "\t {}".format(self.in_csv))
            else:
                self.in_csv = all_csv[0]  

        if self.in_listfile :
            # replace with list file
            all_listfile = UTIL.list_files_by_glob(self.in_listfile,
                                                   sort=True,
                                                   exit_on_miss=True)
            if len(all_listfile) > 1 :
                ab.EP("Too many files found when globbing with:\n"
                      "\t {}".format(self.in_listfile))
            else:
                self.in_listfile = all_listfile[0] 


# ------------------------------------------------------------------

def parse_args(full_argv):
    """Go through user-entered options and fill an object with the values.
    These will be used to setup plotting.

    """

    argv = full_argv[1:]
    Narg = len(argv)

    if not(Narg):
        print(help_string)
        sys.exit(0)

    # initialize objs
    iopts          = iopts_obj()
    iopts.full_cmd = full_argv

    i = 0
    while i < Narg:
        if argv[i] == "{ver}".format(**opts_dict) :
            print(ver)
            sys.exit(0)

        elif argv[i] == "{date}".format(**opts_dict) :
            print(date)
            sys.exit(0)

        elif argv[i] == "{help}".format(**opts_dict) or \
             argv[i] == "{h}".format(**opts_dict) :
            print(help_string_mat_plot)
            sys.exit(0)

        elif argv[i] == "{hview}".format(**opts_dict) :
            prog = os.path.basename(full_argv[0])
            cmd = 'apsearch -view_prog_help {}'.format( prog )
            ab.simple_shell_exec(cmd)
            sys.exit(0)

        # ---------- req ---------------

        # can be a list of many
        elif argv[i] == "{in_mat}".format(**opts_dict) :
            if i >= Narg:
                ab.ARG_missing_arg(argv[i])
            i+= 1
            while i < Narg:
                if opts_list.__contains__(argv[i]) :
                    i-= 1
                    break
                else:
                    iopts.in_mat.append(argv[i])
                    i+= 1

        elif argv[i] == "{prefix}".format(**opts_dict) :
            if i >= Narg:
                ab.ARG_missing_arg(argv[i])
            i+= 1
            iopts.prefix = argv[i]

        # ---------- opt ---------------

        # can be a list of many
        elif argv[i] == "{pars}".format(**opts_dict) :
            if i >= Narg:
                ab.ARG_missing_arg(argv[i])
            i+= 1
            while i < Narg:
                if opts_list.__contains__(argv[i]) :
                    i-= 1
                    break
                else:
                    iopts.pars_list.append(argv[i])
                    i+= 1

        elif argv[i] == "{in_csv}".format(**opts_dict) :
            if i >= Narg:
                ab.ARG_missing_arg(argv[i])
            i+= 1
            iopts.in_csv = argv[i]

        elif argv[i] == "{in_listfile}".format(**opts_dict) :
            if i >= Narg:
                ab.ARG_missing_arg(argv[i])
            i+= 1
            iopts.in_listfile = argv[i]

        # --------- finish -------------

        else:
            print("** ERROR: unknown opt: '{}'".format(argv[i]))
            sys.exit(2)
        i+=1


    if iopts.check_req():
        print("   -------------------------------")
        ab.EP("Problem with input arguments. See detailed whining above.")

    iopts.finish_defs()

    return iopts

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
