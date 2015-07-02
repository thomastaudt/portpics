## portpics.py

Simple python 3 utility script that copies / moves images from an input
folder to an output folder hierarchy. The files may be folder-prefixed by a string
containing %d, %m, or %y for the day, month, or year that the image was
created (it reads this as exif information). The default option is
--prefix="%y/%m/%d". The script can also search for sidecar xmp files and
perform the same copy / move operations on them as for the pictures
themselves.

### Requirements

For the script to work, `import exifread` must succeed in python 3.
Currently only tested for linux (uses `mv`, `mkdir`, and `cp`), but
this is probably subject to change.

### Examples
Example of usage:
```
./portpics.py -i /media/sdc1/DCIM/ -o ~/pictures/jpegs/ -e jpeg -p "%y_%m_%d"
```

### TODO
 * Moving the pictures (instead of copying them) does not work at the moment.
 * The only raw files handled right now are '.srw' files (which is trivial
   to enhance).
 * Maybe get rid of the dependence on exifread
 * Search through subfolders if desired
 * Add compression for jpeg files
 
