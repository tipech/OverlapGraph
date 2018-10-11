"""Apply a version of sweep-line algorithm to overlapping shape data.

Provides sweep-line algorithms for the different shapes of the overlap problem.
Moreover, this can be executed as a script to actually run the algorithms.

Classes:


"""
import sys, argparse, json
import networkx as nx
import matplotlib.pyplot as plt
from shapes import IntervalObject, RectangleObject
from generator import IntervalGenerator, RectangleGenerator
from graphics import Point, Line, Rectangle, Text, GraphWin
from pprint import pprint
from time import sleep



def main():
    """Run an algorithm with command-line parameters."""

    window_size = 1200

    # parser for command line arguments
    parser = argparse.ArgumentParser(
        description="Run a sweep-line algorithm on overlapping shape data.")

    
    # provide options to run with previously generated data or generate new 
    subparsers = parser.add_subparsers()
    load_parser = subparsers.add_parser('load', help="load generated data")
    gen_parser = subparsers.add_parser('generate', help="generate new data")

    # if previous data selected, get file name
    load_parser.add_argument("file", help="generated data file name")

    # optional arguments: print result graph, draw graph
    load_parser.add_argument("-p", "--print", action="store_true",
        help="print results to console")
    load_parser.add_argument("-g", "--graphics", action="store_true",
        help="display graphics and draw results")

    # else, get generator parameters: object type
    gen_parser.add_argument("type", choices=["interval", "rectangle"],
        help="type of overlapping objects")

    # optional arguments: print result graph, draw graph
    gen_parser.add_argument("-p", "--print", action="store_true",
        help="print results to console")
    gen_parser.add_argument("-g", "--graphics", action="store_true",
        help="display graphics and draw results")
    gen_parser.add_argument("-s", "--store", action="store_true",
        help="store generated data to file")

    # extra optional arguments: number of objects, area, min & max size ratios
    gen_parser.add_argument("--number", metavar="N", type=int, default=20,
        help="number of generated objects (default: 20)")
    gen_parser.add_argument("--area", type=int, default=1000,
        help="size of generated area (default: 1000)")
    gen_parser.add_argument("--min", type=float, default=0.01,
        help="min ratio of object size relative to area (def: 0.01)")
    gen_parser.add_argument("--max", type=float, default=0.1,
        help="max ratio of object size relative to area (def: 0.1)")
    
    args = parser.parse_args() # parse the arguments
    

    if "file" in args: # if we selected to load data
        
        algorithm = None

        # try opening the data file
        try:
            with open(args.file, "r") as input_file:
                
                # parse the json data
                data = json.load(input_file)

                # depending on type, load data into generator
                if data['type'] == "interval":
                    generator = IntervalGenerator.from_file(data, window_size)
                    algorithm = IntervalSweepline(generator)

                elif data['type'] == "rectangle":
                    generator = RectangleGenerator.from_file(data, window_size)
                    algorithm = RectangleSweepline(generator)

        # if error occured during file reading, print invalid argument error
        except IOError as e:
            parser.error("Problem occured during file reading: \n\t%s" % e)

    else: # if we selected to generate new data

        # check for invalid numbers
        if args.number < 0 or args.area < 0 or args.min < 0 or args.max < 0 :
            parser.error("Invalid number argument.")
        if args.max > 1 or args.min > args.max :
            parser.error("Invalid ratios.")

        # run generator
        if args.type == "interval":
            generator = IntervalGenerator.from_params(args.number, args.area,
                args.min, args.max, window_size)
            algorithm = IntervalSweepline(generator)
        elif args.type == "rectangle":
            generator = RectangleGenerator.from_params(args.number, args.area,
                args.min, args.max, window_size)
            algorithm = RectangleSweepline(generator)

    # run algorithm
    algorithm.run()

    
    if args.print:  # print results
        print(algorithm.generator)
        pprint(algorithm.final_overlaps)

    if args.store:  # store results
        algorithm.generator.export_data()

    if args.graphics: # draw results
        algorithm.generator.draw(False)
        algorithm.draw()

    




class Sweepline():

    """Create a graph from overlapping shapes using a sweep-line algorithm.

    Superclass that handles the common methods required for the algorithm,
    regardless of object type (shape).
    
    Properties:

    """

    def __init__(self, generator):
        """Prepare space and initialize sweep-line algorithm"""
        self.generator = generator

        self.graph = nx.Graph()


    def draw(self):
        """Draw the generated graph"""

        plt.ion()
        nx.draw_networkx(
            self.graph,
            font_size=14,
            node_size=1,
            node_color="black",
            edge_color="#AAAAAA",
            width=2,
            arrows=False)
        plt.draw()

        # pause drawing for display on screen
        # Note: this is not a fully stable, production level implementation
        try:
            plt.pause(500)
        except Exception as e:
            pass
        
        



class IntervalSweepline(Sweepline):

    """Create the overlapping rectangles graph using a sweep-line algorithm.
    
    Methods:

    """

    def __init__(self, generator):
        """Prepare space and initialize sweep-line algorithm"""
        super().__init__(generator)

        # get all x axis points, store as dictionary with form:
        #    { <point>: [{"object": <object>, "type": start|end}, ...], ...}
        # so different objects that start/end at the same point don't conflict
        self.points_dict = {}
        for interval in generator.objects_dict.values():

            # add node to graph
            self.graph.add_node(interval.id_)
            
            # if there weren't any intervals starting/ending at x_start before
            if interval.start not in self.points_dict.keys():
                self.points_dict[interval.start] = [] # make the array

            self.points_dict[interval.start].append({"object": interval,
                "type": "start"}) # add interval
            
            # if there weren't any intervals starting/ending at x_end before
            if interval.end not in self.points_dict.keys():
                self.points_dict[interval.end] = [] # make the array

            self.points_dict[interval.end].append({"object": interval,
                "type": "end"}) # add interval


        # create list with the points sorted in x axis
        self.points_list = sorted(self.points_dict.keys())


    def run(self):
        """Run the algorithm and generate the overlap graph"""
        
        active_intervals = {} # for intervals that started but haven't ended
        active_overlaps = []  # for overlaps that started and haven't ended
        self.final_overlaps = []  # for overlaps that ended

        for current_point in self.points_list: # sweep through points

            # find intervals that start/end at current 
            point_intervals = self.points_dict[current_point]
            for point_interval in point_intervals:

                interval_object = point_interval['object']

                # if interval just started
                if point_interval['type'] == "start":

                    # loop through previous active overlaps and add new object
                    for previous_interval in active_intervals.values():

                        # new overlap details
                        active_overlaps.append({
                            '1': interval_object.id_,
                            '2': previous_interval.id_,
                            'start': current_point })

                    # start tracking interval
                    active_intervals[interval_object.id_] = interval_object

                # if interval is ending
                elif point_interval['type'] == "end":

                    # rect no longer active
                    del active_intervals[interval_object.id_]

                    # terminate all overlaps this interval was in
                    #   reversed to prevent corruption when deleting items
                    for overlap in reversed(active_overlaps):
                        if (overlap['1'] == interval_object.id_ 
                            or overlap['2'] == interval_object.id_):

                            # calculate overlap length
                            overlap['length'] = (current_point
                                - overlap['start'])

                            # add graph edge for overlap
                            self.graph.add_edge(overlap['1'], overlap['2'])

                            # store overlap in results, remove from active
                            self.final_overlaps.append(overlap)
                            active_overlaps.remove(overlap)




class RectangleSweepline(Sweepline):

    """Create the overlapping rectangles graph using a sweep-line algorithm.
    
    Methods:

    """

    def __init__(self, generator):
        """Prepare space and initialize sweep-line algorithm"""
        super().__init__(generator)

        # get all x axis points, store as dictionary with form:
        #    { <point>: [{"object": <object>, "type": start|end}, ...], ...}
        # so different objects that start/end at the same point don't conflict
        self.points_dict = {}
        for rectangle in generator.objects_dict.values():

            # add node to graph
            self.graph.add_node(rectangle.id_)
            
            # if there weren't any rectangles starting/ending at x1 before
            if rectangle.x1 not in self.points_dict.keys():
                self.points_dict[rectangle.x1] = [] # make the array

            self.points_dict[rectangle.x1].append({"object": rectangle,
                "type": "start"}) # add rectangle
            
            # if there weren't any rectangles starting/ending at x2 before
            if rectangle.x2 not in self.points_dict.keys():
                self.points_dict[rectangle.x2] = [] # make the array

            self.points_dict[rectangle.x2].append({"object": rectangle,
                "type": "end"}) # add rectangle


        # create list with the points sorted in x axis
        self.points_list = sorted(self.points_dict.keys())


    def run(self):
        """Run the algorithm and generate the overlap graph"""
        
        active_rects = {}    # for rectangles that started but haven't ended
        active_overlaps = [] # for overlaps that started and haven't ended
        self.final_overlaps = []  # for overlaps that ended

        for current_point in self.points_list: # sweep through points

            # find rects that start/end at current point and perform action
            point_rects = self.points_dict[current_point]
            for point_rect in point_rects:

                rect_object = point_rect['object']

                # if rectangle just startedand there are existing active ones
                if point_rect['type'] == "start":

                    if len(active_rects) > 0:
                        # check for new overlaps and add them to the actives
                        new_overlaps = self._check_overlaps(rect_object,
                            active_rects, current_point)
                        active_overlaps += new_overlaps

                    # start tracking rectangle
                    active_rects[rect_object.id_] = rect_object

                # if rectangle is ending
                elif point_rect['type'] == "end":

                    # rect no longer active
                    del active_rects[rect_object.id_]

                    # terminate all overlaps this rectangle was in
                    #   reversed to prevent corruption when deleting items
                    for overlap in reversed(active_overlaps):
                        if (overlap['1'] == rect_object.id_ 
                            or overlap['2'] == rect_object.id_):

                            # calculate overlap x axis length and total area
                            overlap['x_length'] = (current_point
                                - overlap['x_start'])
                            overlap['area'] = (overlap['x_length']
                                * overlap['y_length'])

                            # add graph edge for overlap
                            self.graph.add_edge(overlap['1'], overlap['2'])

                            # store overlap in results, remove from active
                            self.final_overlaps.append(overlap)
                            active_overlaps.remove(overlap)


    def _check_overlaps(self, new_rect, active_rects, current_point):
        """Checks if rectangle overlaps with actives and returns overlaps"""

        new_overlaps = []
        overlap_length = 0

        for possible_rect in active_rects.values(): # compare new with actives

            if (new_rect.y1 > possible_rect.y1 
                and new_rect.y1 < possible_rect.y2
                and new_rect.y2 > possible_rect.y2):
                # overlapping, new below (and to the right) of old

                overlap_length = possible_rect.y2 - new_rect.y1

            elif (new_rect.y1 < possible_rect.y1 
                and new_rect.y2 > possible_rect.y1
                and new_rect.y2 < possible_rect.y2):
                # overlapping, new above (and to the right) of old

                overlap_length = new_rect.y2 - possible_rect.y1

            elif (new_rect.y1 < possible_rect.y1 
                and new_rect.y2 > possible_rect.y2):
                # overlapping, new within old

                overlap_length = new_rect.y2 - new_rect.y1

            elif (new_rect.y1 > possible_rect.y1 
                and new_rect.y2 < possible_rect.y2):
                # overlapping, old within new

                overlap_length = possible_rect.y2 - possible_rect.y1

            if overlap_length > 0: # successful overlap

                # add overlap item
                new_overlaps.append({
                    '1': possible_rect.id_,
                    '2': new_rect.id_,
                    'y_length': overlap_length,
                    'x_start': current_point })

        return new_overlaps




if __name__ == "__main__":
    # Run the module with command-line parameters.
    main()