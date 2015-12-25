#!/usr/bin/env python3

#TODO:
    #   o testing
    #   o compression?
    #   o ssh-support?

# standard modules
from sys          import exit, stderr
from shutil       import copy, copy2, move
from os           import path, walk, makedirs
from glob         import glob
from subprocess   import call
from functools    import reduce
from argparse     import ArgumentParser

# non-standard modules
from exifread     import process_file


def get_supported_extensions():
    # List of all raw formats
    pic_exts_raw = [ 
                     "srw", "3fr", "ari", "arw", "srf", "sr2", "bay", "crw",
                     "cr2", "cap", "iiq", "eip", "dcs", "dcr", "drf", "k25",
                     "kdc", "dng", "erf", "fff", "mef", "mdc", "mos", "mrw",
                     "nef", "nrw", "orf", "pef", "ptx", "pxn", "r3d", "raf",
                     "rw2", "rwl", "rwz", "x3f"
                   ]
    # Collect all possible picture extensions in a dict
    pic_exts = {
                     "jpg"  : ["jpg", "JPG", "jpeg", "JPEG"],
                     "png"  : ["png", "PNG"],
                     "tiff" : ["tiff", "TIFF"],
                     "raw"  : ["raw", "RAW"] + 
                              pic_exts_raw   + 
                              list(map(lambda x: x.upper(), pic_exts_raw))
               }
    # For case-sensitive file systems
    for ext in pic_exts_raw: pic_exts[ext] = [ext, ext.upper()]
    
    # List of sidecar extensions
    sidecar_exts = [ 
                     "xmp", "XMP" 
                   ]

    return pic_exts, sidecar_exts



def get_options(supported_extensions):
    parser = ArgumentParser("Portpics -- Copy/move image files based on exif date information")
    # string options
    parser.add_argument("-i", "--indir",      dest="indir"                         )
    parser.add_argument("-o", "--outdir",     dest="outdir"                        )
    parser.add_argument("-e", "--extensions", dest="exts",     default="jpg"       )
    parser.add_argument("-n", "--name",       dest="name",     default='%f'        )
    parser.add_argument("-c", "--command",    dest="command",  default=''          )
    parser.add_argument("-D", "--digits",     dest="digits",   default=0, type=int )
    parser.add_argument("-O", "--offset",     dest="offset",   default=0, type=int )
    # flags
    parser.add_argument("-R", "--recursive",  dest="recursive", action="store_true", default=False)
    parser.add_argument("-s", "--sidecar",    dest="sidecar",   action="store_true", default=False)
    parser.add_argument("-v", "--verbose",    dest="verbose",   action="store_true", default=False)
    parser.add_argument("-q", "--quiet",      dest="quiet",     action="store_true", default=False)
    parser.add_argument("-r", "--replace",    dest="replace",   action="store_true", default=False)
    parser.add_argument("-d", "--delete",     dest="delete",    action="store_true", default=False)

    # Create the options object to be returned
    options = parser.parse_args()

    # Before doing so, some sanity checks:
    # Input directory must be specified and existent
    if (options.indir  is None):
        error_msg("Directory containing the input files must be specified, see --help")
    elif not path.isdir(options.indir):
        error_msg("Input directory '%s' does not exist" % options.indir)

    # Output directory must be specified
    if (options.outdir is None):
        error_msg("Target directory for the output files must be specified, see --help")

    # Check if all given extensions are 'supported'
    options.exts = options.exts.split(",") # if several extensions are given simultaneously
    if any(ext not in supported_extensions[0] for ext in options.exts):
        error_msg("At least one of the given extensions %s is not supported." % (tuple(options.exts)),)

    # Collect all extensions that are interesting
    options.pic_exts = reduce( 
                               lambda a,b: a + b, 
                               [supported_extensions[0][ext] for ext in options.exts], 
                               []
                             )
    options.sidecar_exts = supported_extensions[1]
    if options.verbose: 
        print(
               "Files with the following extensions will be processed:\n  %s" % 
               "\n  ".join(options.pic_exts)
             )

    return options



def get_filenames(options):
    # Construct the wildcard-patterns then feeded to glob in order to obtain all files
    if not options.recursive:
        patterns = [ path.join(options.indir, "*.%s" % ext) for ext in options.pic_exts ]
    else:
        patterns = [ path.join(directory[0], "*.%s" % ext) for ext in options.pic_exts 
                                                           for directory in walk(options.indir) ]

    # Collect all file names
    fnames = []
    for pattern in patterns: fnames.extend(glob(pattern))
    fnames.sort()

    # Print some info if desired
    if fnames == []: error_msg("No files with the specified extensions found")
    if options.verbose: 
        print( 
               "\nFound %d matching file/files\n" % len(fnames) +
               "\n" + "\n".join("  " + f for f in fnames)
             )
    return fnames



def create_datemap(fnames, options):
    datemap   = {}
    for fname in fnames:
        f = open(fname, 'rb')
        tags = process_file(f, details=False, stop_tag="DateTimeOriginal", strict=True)
        try: 
            date = tuple(map(int, tags['EXIF DateTimeOriginal'].printable.split(' ')[0].split(':')))
        except KeyError:
            warn_msg("Exif tag 'DateTimeOriginal' could not be read in file %s. This file will not be processed!" % fname)
            continue
        if date in datemap: datemap[date].append(fname)
        else: datemap[date] = [fname]

    if options.verbose: 
        print(
               "\nCreated datemap with %d different date/dates:\n  %s" % 
               (len(datemap), "\n  ".join([str(key) for key in datemap.keys()]))
             )
    return datemap



def process_pictures(datemap, options, num_total):
    # Count how many pictures have been processed so that a percentage can be printed
    num_current = 0
    if options.verbose: print("\nProcessing:")

    # Go through every date, and process the corresponding pictures
    for date, inpaths in datemap.items():
        # Prepare replacement of placeholders (like %y) with actual numbers (like 2013)
        date_repls = ("%y", "%04d" % date[0]), ("%m", "%02d" % date[1]), ("%d", "%02d" % date[2])

        # Apply successive replaces to replace the date placeholders
        outfolder = reduce(lambda a,b: a.replace(*b), date_repls, options.outdir) 

        # Create the folder and process the pictures that are to be copied/moved to it
        create_folder(outfolder)
        for inpath in inpaths:
            num_current = num_current + 1
            process_picture(inpath, date_repls, outfolder, options, num_current, num_total)

    # Message to signal that the program finished
    log_msg(options, "\nDone! (Processed %d pictures)\n" % num_total)


def process_picture(inpath, date_repls, outfolder, options, num_current, num_total):
    # The markers %y, %m, %d, %f, %n shall be replaced by 
    # year, month, day, (orig) filname and num_current for the new filename
    nd = str(options.digits if options.digits != 0 else len(str(num_total + options.offset)))
    repls = date_repls + (("%f", path.basename(inpath)), ("%n", ("%0" + nd + "d") % (num_current + options.offset)))
    outname = reduce(lambda a,b: a.replace(*b), repls, options.name)

    # Get the full destination path for the picture
    outpath = path.join(outfolder, outname)

    # If a command (some shell command to be carried out after
    # copying/moving the picture) is provided, prepare it suitably
    command = options.command
    if command != "": 
        # The markers %y, %m, %d, %f, %n shall be replaced by 
        # year, month, day, (new) filname and num_current for the command
        crepls = date_repls + (("%f", outname), ("%n", str(num_current)))
        command = reduce(lambda a,b: a.replace(*b), repls, command)

    # All preparations completed; now copy/move the files
    if options.replace or not path.isfile(outpath):
        perc = num_current/num_total*100
        msg = "%3d%%%%: %s  '%s'  to  '%s'" % (perc, "%s", path.basename(inpath), outpath) 
        if options.delete: 
            log_msg(options, msg % "Move")
            move_file(inpath, outpath) 
        else:
            log_msg(options, msg % "Copy")
            copy_file(inpath, outpath) 
        if command != "":
            log_msg(options, ("%3d%%" % perc) + command)
            call(command.split())

    # handle sidecar files
    if options.sidecar: process_sidecar(inpath, outpath, options)


def process_sidecar(inpath, outpath, options):
    possible_sidecar_files = [ inpath + "." + ext for ext in sidecar_exts ]
    for sidecar_file in possible_sidecar_files: 
        outpath = path.join(outfolder, path.basename(sidecar_file))
        if path.isfile(sidecar_file): 
            if options.delete: move_file(sidecar_file, outpath)
            else:              copy_file(sidecar_file, outpath)




def create_folder(folder):
    makedirs(folder, exist_ok=True)

def copy_file(src, dest):
    copy2(src, dest)

def move_file(src, dest):
    move(src, dest)

def log_msg(options, text):
    # This is not nice...
    if not options.quiet: print(text, end="\r")

def error_msg(text):
    print("Error:", text, file=stderr)
    exit()

def warn_msg(text):
    print("Warning:", text, file=stderr)


def portpics():
    # 
    exts = get_supported_extensions()
    # Parse the command line arguments for options
    options = get_options(exts)
    # Determine which glob-wildcards shall be used to identify the files
    filenames = get_filenames(options)
    # Create the 'datemap', which maps dates on lists of source
    # files that are to be copied to the respective destiny folders
    datemap = create_datemap(filenames, options)
    # Do the processing
    process_pictures(datemap, options, len(filenames))


if __name__ == "__main__": portpics()
