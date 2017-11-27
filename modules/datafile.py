#!/usr/bin/env python
"""
Datafile object for tracklog and Loc file.

(C) 2016-2017 1024jp
"""

import csv
import os


# constants
LOC_FILENAME = "Location.csv"
DEFAULT_INPUT_COLUMNS = (2,3)
FIND_LEVEL = 3  # number of parent directories to find in.


class Data:
    def __init__(self, datafile, z=None, in_cols=None, out_cols=None):
        """Initialize Data object.

        Arguments:
        datafile (file) -- main data file in file-like object form.
        z_filter (int) -- Z-axis in destination points to obtain.
        in_cols (int, int) -- column indexes of x,y coordinates in datafile.
        out_cols (int, int) -- column indexes of x,y coordinates for calibrated
                               data.
        """
        # sanitize path
        self.datafile = datafile
        self.dirpath = os.path.dirname(datafile.name)

        # load Loc file
        self.loc_path = self._find_file(LOC_FILENAME)[0]
        image_points, dest_points = self._load_location(z_filter=z)
        self.image_points = image_points
        self.dest_points = dest_points

        self.in_cols = in_cols or DEFAULT_INPUT_COLUMNS
        self.out_cols = self.in_cols

    def _find_file(self, filename, subdirectory=None):
        """Find file in the same directory and also parent directories

        Arguments:
        filename (str) -- filename.
        subdirectory (str) -- directory where file is located.
        """
        paths = []
        dirpath = self.dirpath
        for _ in range(FIND_LEVEL):
            components = [dirpath, filename]
            if subdirectory:
                components.insert(subdirectory)
            path = os.path.join(*components)
            if os.path.exists(path):
                paths.append(path)
            dirpath = os.path.dirname(dirpath)

        return paths

    def _load_location(self, z_filter=None):
        """Load location definition file.

        Returns:
        image_points -- x,y pairs of reference points in image.
        dest_points -- corresponding x,y pairs of ref points in field.
        """
        image_points = []
        dest_points = []
        with open(self.loc_path, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if len(row) < 4:
                    continue
                first_char = row[0][0]
                if first_char.isalpha() or first_char is '#':
                    continue
                row = list(map(float, row))
                image_point = row[3:5]
                dest_point = row[0:3]
                if z_filter and dest_point[2] != z_filter:
                    continue
                image_points.append(image_point)
                dest_points.append(dest_point[0:2])

        return image_points, dest_points

    def file_named(self, filename, exists=False):
        path = os.path.join(self.dirpath, filename)
        if exists and not os.path.exists(path):
            return None
        return path

    def process_coordinates(self, processor_handler, output):
        in_cols = self.in_cols
        out_cols= self.out_cols
        
        with open(self.datafile.name) as file_in:
            # detect delimiter
            dialect = csv.Sniffer().sniff(file_in.read(2048), delimiters=',\t')
            file_in.seek(0)

            reader = csv.reader(file_in, dialect)
            writer = csv.writer(output, dialect)

            for row in reader:
                new_row = row[:]  # copy

                try:
                    x = float(row[in_cols[0]])
                    y = float(row[in_cols[1]])
                except:  # go to next column if not number
                    writer.writerow(new_row)
                    continue

                # translate
                x, y = processor_handler(x, y)

                new_row[out_cols[0]] = int(x)
                new_row[out_cols[1]] = int(y)

                writer.writerow(new_row)
