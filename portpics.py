#!/usr/bin/env python3

# TODO: make this script independend of non-standard packages (i.e. remove
# exifread)

from optparse import OptionParser
from glob import glob
from os import path
from subprocess import call
from exifread import process_file
from warnings import warn


pic_exts = { 
             "jpg" : ["jpg", "JPG", "jpeg", "JPEG"],
             "raw" : ["srw", "SRW"],
             "png" : ["png", "PNG"]
           }

sidecar_exts = [ 
                 "xmp", "XMP" 
               ]

def get_options():
    parser = OptionParser()
    # string options
    parser.add_option("-i", "--indir",     dest="indir",   type="string")
    parser.add_option("-o", "--outdir",    dest="outdir",  type="string")
    parser.add_option("-e", "--extension", dest="ext",     type="string", default="jpg")
    parser.add_option("-p", "--prefix",    dest="prefix",  type="string", default='%y/%m/%d')
    # flags
    parser.add_option("-d", "--delete",    dest="delete",  action="store_true", default=False)
    parser.add_option("-s", "--sidecar",   dest="sidecar", action="store_true", default=False)
    parser.add_option("-v", "--verbose",   dest="verbose", action="store_true", default=False)
    parser.add_option("-r", "--replace",   dest="replace", action="store_true", default=False)
    # create th options object to be returned
    options, args = parser.parse_args()
    # before doing so, some sanity checks
    if (options.indir  is None):   raise Exception("Directory containing the input files must be specified, see --help")
    if (options.outdir is None):   raise Exception("Target directory for the output files must be specified, see --help")
    if options.ext not in pic_exts: raise Exception("Extension not recognized: %s" % options.ext)
    # 
    return options

def get_filenames(options):
    # TODO: sub-directories!
    # construct the wildcard-patterns then feeded to glob in order to obtain all files
    patterns = [ path.join(options.indir, "*.%s" % ext) for ext in pic_exts[options.ext] ]
    # collect all file names
    fnames = []
    for pattern in patterns: fnames.extend(glob(pattern))
    fnames.sort()
    # some info if desired
    if options.verbose: print("Found %d files:" % len(files), "\n", "\n".join(f for f in files))
    return fnames

def copy_or_move(picture, outfolder, options):
    outfile = path.join(outfolder, path.basename(picture))
    # TODO: implement all options here
    # TODO: make this independent of OS
    # TODO: should probably copy/move all files in one command
    #if options.delete and options.replace:
        #print("\t%s  ->  %s" % (picture, outfile))
        ##call(["mv", picture, outfile])
    #if options.delete and not options.replace:
        #if path.isfile(outfile):
            #print("\t%s  ==  %s" % (picture, outfile))
        #else:
            #print("\t%s  ->  %s" % (picture, outfile))
            ##call(["mv", picture, outfile])
    if not options.delete and options.replace:
        print("  %s  =>  %s" % (picture, outfile))
        call(["cp", picture, outfile])
    if not options.delete and not options.replace:
        if path.isfile(outfile):
            print("  %s  ==  %s" % (picture, outfile))
        else:
            print("  %s  =>  %s" % (picture, outfile))
            call(["cp", picture, outfile])


def copy_or_move_sidecar(picture, outfolder, options):
    possible_sidecar_files = [ picture + ext for ext in sidecar_exts ]
    for sidecar_file in possible_sidecar_files: 
        if path.isfile(sidecar_file): 
            copy_or_move(sidecar_file, outfolder, options)


# the foldermap is a dict, that maps target folder names to lists of source
# files that are to be copied to the target folders
def create_foldermap(fnames, options):
    foldermap = {}
    for fname in fnames:
        f = open(fname, 'rb')
        tags = process_file(f, details=False, stop_tag="DateTimeOriginal", strict=True)
        try: 
            year, month, day, h,m,s = tags['EXIF DateTimeOriginal'].printable.replace(" ", ":").split(':')
        except KeyError:
            warn("File %s could not be processed!" % fname)
            continue
        outfolder = path.join(options.outdir, options.prefix.replace("%y", year).replace("%m", month).replace("%d", day))
        if outfolder in foldermap.keys(): foldermap[outfolder].append(fname)
        else: foldermap[outfolder] = [fname]
    return foldermap

def create_folder(folder):
    print()
    if not path.isdir(folder):
        print("Create folder %s" % folder)
    else:
        print("%s:" % folder)
        print("-" * (1 + len(folder)))
    call(["mkdir", "-p", folder])

def overview():
    print()
    print(" == : file already existed; not replaced")
    print(" => : file was copied")
    print(" -> : file was moved")

def portpics():
    # parse the command line arguments for options
    options = get_options()
    # determine which glob-wildcards shall be used to identify the files
    filenames = get_filenames(options)
    # create the 'foldermap', which maps destiny-folders on lists of source
    # files that are to copied to the respective destiny folders
    foldermap = create_foldermap(filenames, options)
    #
    for outfolder in foldermap:
        create_folder(outfolder)
        for picture in foldermap[outfolder]:
            copy_or_move(picture, outfolder, options)
            if options.sidecar: 
                copy_or_move_sidecar(picture, outfolder, options)
    overview()


if __name__ == "__main__": portpics()
