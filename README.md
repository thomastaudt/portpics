## portpics.py
Copy pictures to folders based on their exif date information.

Simple python3 utility script that copies or moves images from an input
folder to an output folder hierarchy that may depend on exif date
information of the pictures. This means that the specified output folder
may contain the placeholders '%d', '%m', or '%y' for the day, month, or
year of the images 'EXIF DateTimeOriginal' information. The script can
also search for sidecar (.xmp) files and perform the same copy / move
operations on them as on the pictures.

One can also specify a command to be run after copying the single
files, so that the pictures may e.g. be compressed.

### Requirements

For the script to work, `from exifread import process_file` must succeed in
Python 3.2 or above (this requires the `exifread` package).
The script should work on every OS reasobably supported by python, but only
linux is tested by the author.

### Options

```
Placeholders:

%y: year
%m: month
%d: day
%f: file name
%n: processing number (each picture to be processed obtains such a number)


Usage: Portpics -- Copy/move image files based on exif date information
       [-h] [-i INDIR] [-o OUTDIR] [-e EXTS] [-n NAME] [-c COMMAND]
       [-D DIGITS] [-O OFFSET] [-R] [-s] [-v] [-q] [-r] [-d]


-i,--input         input directory
-o,--output        output directory
-e,--extensions    comma separated list of file extensions that are
                   searched for in the input directory [default: jpg]
-n,--name          name of the output files; may contain %y,%m,%d,%f,%n;
                   in this case %f is the basename of the original
                   target file [default: %f]
-c,--command       command that shall be applied on the copied files;
                   may contain %y,%m,%d,%f,%n; in this case %f is the
                   basename of the copied file
-D,--digits        number of digits that %n is replaced with; e.g. for
                   10 pictures and -p 3 the values of %n would go from
                   001 to 010 [default: digits of number of pictures]
-O,--offset        offset of %n; -O 10 would mean that %n starts at 11
                   instead of at 1. (-D and -O allow to get a consistent
                   numbering with %n between different runs of portpics)
                   [default: 0]

-R,--recursive     flag; if given the input directory is searched
                   recursively
-s,--sidecar       flag; if given sidecar files (.xmp, .XMP) are also
                   copied / moved
-v,--verbose       flag; if given more informations are printed
-q,--quiet         flag; causes the script to run quietly
-r,--replace       flag; if given target files that already exist are
                   overwritten (by default they are not!)
-d,--delete        flag; if given the pictures are moved to their
                     destination instead of copied.
```

### Examples

Examples of usage:
```
./portpics.py -i /media/mmcblk0p1/DCIM/ -o ~/pictures/%y/%m/%d -e jpg,raw
./portpics.py -i ... -o ... -e jpg -c 'convert %f -resize 2000 -quality 70% small_%f'
```

### TODO
 * testing (especially, if shutils.copy2 is the right choice)...
 * Compression?
 * SSH?
 * Sort by date so that %n is deterministic on the pictures
