#!/usr/bin/env python3

# TODO: make this script independend of non-standard packages (i.e. remove
# exifread)

from optparse import OptionParser
from glob import glob
from os import path, walk
from subprocess import call
from exifread import process_file
from warnings import warn
from sys import stdout
from functools import reduce


def get_supported_extensions():
    # List of all raw formats
    pic_exts_raw = [ 
                     "srw", "3fr", "ari", "arw", "srf", "sr2", "bay", "crw",
                     "cr2", "cap", "iiq", "eip", "dcs", "dcr", "drf", "k25",
                     "kdc", "dng", "erf", "fff", "mef", "mdc", "mos", "mrw",
                     "nef", "nrw", "orf", "pef", "ptx", "pxn", "r3d", "raf",
                     "rw2", "rwl", "rwz", "x3f"
                   ]
    # collect all possible picture extensions in a dict
    pic_exts = {
                     "jpg"  : ["jpg", "JPG", "jpeg", "JPEG"],
                     "png"  : ["png", "PNG"],
                     "tiff" : ["tiff", "TIFF"],
                     "raw"  : ["raw", "RAW"] + pic_exts_raw + list(map(lambda x: x.upper(), pic_exts_raw))
               }
    for ext in pic_exts_raw: pic_exts[ext] = [ext, ext.upper()]
    
    # List of sidecar extensions
    sidecar_exts = [ 
                     "xmp", "XMP" 
                   ]
    return pic_exts, sidecar_exts



def get_options(supported_extensions):
    parser = OptionParser()
    # string options
    parser.add_option("-i", "--indir",      dest="indir",   type="string")
    parser.add_option("-o", "--outdir",     dest="outdir",  type="string")
    parser.add_option("-e", "--extensions", dest="exts",    type="string", default="jpg")
    parser.add_option("-n", "--name",       dest="name",    type="string", default='%f')
    parser.add_option("-c", "--command",    dest="command", type="string", default='')
    parser.add_option("-p", "--digits",     dest="digits",  type="int",    default=0)
    # flags
    parser.add_option("-R", "--recursive",  dest="recursive", action="store_true", default=False)
    parser.add_option("-s", "--sidecar",    dest="sidecar",   action="store_true", default=False)
    parser.add_option("-v", "--verbose",    dest="verbose",   action="store_true", default=False)
    parser.add_option("-q", "--quiet",      dest="quiet",     action="store_true", default=False)
    parser.add_option("-r", "--replace",    dest="replace",   action="store_true", default=False)
    parser.add_option("-d", "--delete",     dest="delete",    action="store_true", default=False)
    # Create th options object to be returned
    options, args = parser.parse_args()
    # Before doing so, some sanity checks
    # Input directory must be specified
    if (options.indir  is None):
        raise Exception("Directory containing the input files must be specified, see --help")
    elif not path.isdir(options.indir):
        raise Exception("Input directory '%s' does not exist" % options.indir)
    # Output directory must be specified
    if (options.outdir is None):
        raise Exception("Target directory for the output files must be specified, see --help")
    # Check if all given extensions are 'supported'
    options.exts = options.exts.split(",") # if several extensions are given simultaneously
    if any(ext not in supported_extensions[0] for ext in options.exts):
        raise Exception("At least one of the given extensions %s is not supported." % (tuple(options.exts)),)
    # Collect all extensions that are interesting
    options.pic_exts = reduce(lambda a,b: a + b, [supported_extensions[0][ext] for ext in options.exts], [])
    options.sidecar_exts = supported_extensions[1]
    if options.verbose: print("Files with the following extensions will be processed:\n  %s" % options.pic_exts)
    # Okay, should be good to go
    return options

def get_filenames(options):
    # construct the wildcard-patterns then feeded to glob in order to obtain all files
    if not options.recursive:
        patterns = [ path.join(options.indir, "*.%s" % ext) for ext in options.pic_exts ]
    else:
        patterns = [ path.join(directory[0], "*.%s" % ext) for ext in options.pic_exts for directory in walk(options.indir) ]
    # collect all file names
    fnames = []
    for pattern in patterns: fnames.extend(glob(pattern))
    fnames.sort()
    # some info if desired
    if options.verbose: print("Found %d matching files:" % len(fnames) + "\n" + "\n".join("  "+f for f in fnames))
    return fnames


def process_picture(inpath, date_repls, outfolder, options, num_current, num_total):
    # The markers %y, %m, %d, %f, %n shall be replaced by 
    # year, month, day, (orig) filname and num_current for the new filename
    num_digits = str(options.digits if options.digits != 0 else len(str(num_total)))
    repls = date_repls + (("%f", path.basename(inpath)), ("%n", ("%0" + num_digits + "d") % num_current))
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

    # All preparations completed; copy/move the files
    if options.delete:
        #TODO
        print("Option delete not yet implemented")
        pass
    else:
        if options.replace:
            log(options, "%3d%%: Copy   %s   to   %s" % (num_current/num_total*100, path.basename(inpath), outpath))
            copy_file(inpath, outpath)
            if command != "":
                log(options, command)
                call(command.split())
        else:
            if not path.isfile(outpath):
                log(options, "%3d%%: Copy   %s   to   %s" % (num_current/num_total*100, path.basename(inpath), outpath))
                copy_file(inpath, outpath)
                if command != "":
                    log(options, ("%3d%%: " % num_current/num_total*100) + command)
                    call(command.split())
    # handle sidecar files if specified
    if options.sidecar: process_sidecar(inpath, outpath, options)


def process_sidecar(inpath, outpath, options):
    possible_sidecar_files = [ inpath + "." + ext for ext in sidecar_exts ]
    for sidecar_file in possible_sidecar_files: 
        outpath = path.join(outfolder, path.basename(sidecar_file))
        if path.isfile(sidecar_file): 
            if options.delete:
                #TODO
                print("Option delete not yet implemented")
                pass
            else:
                copy_file(sidecar_file, outpath)


# the foldermap is a dict, that maps target folder names to lists of source
# files that are to be copied to the target folders
def create_datemap(fnames, options):
    datemap   = {}
    #foldermap = {}
    for fname in fnames:
        f = open(fname, 'rb')
        tags = process_file(f, details=False, stop_tag="DateTimeOriginal", strict=True)
        try: 
            date = tuple(map(int, tags['EXIF DateTimeOriginal'].printable.split(' ')[0].split(':')))
        except KeyError:
            warn("Exif tag 'DateTimeOriginal' could not be read in file %s. This file will not be processed!" % fname)
            continue
        if date in datemap: datemap[date].append(fname)
        else: datemap[date] = [fname]

    if options.verbose: print("Created datemap with %d different dates." % len(datemap))
    return datemap


def process_pictures(datemap, options, num_total):
    # Count how many pictures have been processed so that a percentage can be printed
    num_current = 0
    if options.verbose: print("\nProcessing:", end="")
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
    log(options, "\nDone!")


def create_folder(folder):
    call(["mkdir", "-p", folder])

def copy_file(src, dest):
    call(["cp", src, dest])

def move_file(src, dest):
    call(["mv", src, dest])

def log(options, text):
    if not options.quiet: print(text, end="\r")


def portpics():
    exts = get_supported_extensions()
    # parse the command line arguments for options
    options = get_options(exts)
    # determine which glob-wildcards shall be used to identify the files
    filenames = get_filenames(options)
    # create the 'datemap', which maps dates on lists of source
    # files that are to be copied to the respective destiny folders
    datemap = create_datemap(filenames, options)
    #
    process_pictures(datemap, options, len(filenames))


if __name__ == "__main__": portpics()
