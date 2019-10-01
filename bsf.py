from math import sqrt
from heapq import heapify, heappush, heappop
import json, time, codecs, sys, ast, os

MINIFIED_CSS = """
        body,
        html {
            width: 100%;
            height: 100%;
            background: gray;
        }

        .branch {
            display: flex;
            flex-direction: column;
            flex: 1;
        }

        .branch__root {
            display: flex;
            justify-content: center;
            align-content: center;
        }

        .branch__leafs {
            display: flex;
        }

        .state {
            margin: 50px;
            display: inline-block;
            position: relative;
            background: #000;
            width: 75px;
        }

        .state td {
            background: #fff;
            width: 20px;
            line-height: 20px;
            text-align: center;
        }
        .state svg {
            position: absolute;
        }
        td.empty-space {
            background: black;
        }

        .solution-path {
            background: red;
        }

        .branch table {
            border-spacing: 5px;
            border-collapse: separate;
        }
        .search-stats {
            z-index: 1000;
            position: fixed;
            top: 0;
            left: 0;
            display: inline-block;
            padding: 5px;
            background: white;
        }
        .search-stats span {
            font-size: 2em;
        }
        .state-info {
            visibility: hidden;
            text-align: center;
            padding: 5px;
            color: white;
            position: absolute;
            z-index: 1;
            background: black;
            border-radius: 6px;
            width: 110px;
            top: -50px;
            left: 50px;
        }
        .state-info:before {
            content: '';
            display: block;
            width:0;
            height:0;
            position:absolute;
            border-top: 8px solid black;
            border-bottom: 8px solid transparent; 
            border-right:8px solid transparent;
            border-left:8px solid transparent;
            left: 5px;
            top: 43px;
        }
        .state:hover .state-info {
            visibility: visible;
        }
"""
MINIFIED_JS = """
        function draw_connections($branch) {
            function draw_connection($parentState, $childState) {
                var parentOffset = $parentState.offset();
                var childOffset = $childState.offset();
                svgBoxWidth = Math.abs((parentOffset.left + ($parentState.width() / 2)) - (childOffset.left + ($childState.width() / 2))) + 2;
                svgBoxHeight = Math.abs((parentOffset.top + $parentState.height()) - childOffset.top);
                var is_in_left_of_parent = () => childOffset.left < parentOffset.left
                var new_$line = function ($line) {
                    var $line = $(document.createElementNS('http://www.w3.org/2000/svg', 'line')).attr('stroke-width', '3').attr('stroke', $childState.hasClass('solution-path') ? 'red' : 'black');
                    if (is_in_left_of_parent()) {
                        $line.attr('x1', svgBoxWidth).attr('y1', 0).attr('x2', 0).attr('y2', svgBoxHeight);
                    } else {
                        $line.attr('x1', 0).attr('y1', 0).attr('x2', svgBoxWidth).attr('y2', svgBoxHeight);
                    }
                    return $line;
                }
                $(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
                    .attr('width', svgBoxWidth)
                    .attr('height', svgBoxHeight)
                    .css({
                        width: svgBoxWidth,
                        height: svgBoxHeight,
                        left: is_in_left_of_parent() ? ((childOffset.left - parentOffset.left) + ($parentState.width() / 2)) : ($parentState.width() / 2)
                    })
                    .append(new_$line())
                    .appendTo($parentState);
            }
            var get_$root_state_of_branch = (branch) => $(branch).find('.branch__root').eq(0).children();
            var get_$children_branches_of_branch = (branch) => $(branch).find('.branch__leafs').eq(0).children();
            var $rootState = get_$root_state_of_branch($branch);
            var rootOffset = $rootState.offset();
            var $childrenBranches = get_$children_branches_of_branch($branch);
            if ($childrenBranches) {
                $childrenBranches.each((idx, childBranch) => {
                    draw_connection($rootState, get_$root_state_of_branch(childBranch));
                    draw_connections(childBranch);
                })
            }
        }
        function get_state_info(state) {
            var state_info = $('<div class="state-info">');
            state_info.text('Heurística: ' + state.heuristic_score + ' Profundidade: ' + state.depth);
            return state_info;
        }
        function new_state(state) {
            var new_row = () => $('<tr>');
            var new_tile = (tile) => $('<td>').text(tile).addClass(tile == 0 ? 'empty-space' : '');
            var rows = Math.sqrt(state.tiles.length);
            var $table = $('<table>');
            var $row = new_row();
            state.tiles.forEach((tile, idx) => {
                $row.append(new_tile(tile));
                if ((idx + 1) % rows == 0) {
                    $table.append($row);
                    $row = new_row();
                }
            });
            return $('<div>')
                .attr('class', state.solution_path ? 'state solution-path' : 'state')
                .append(get_state_info(state))
                .append($table)
        }
        function draw_branch(state) {
            var new_$div = (classes) => classes ? $('<div>').attr('class', classes) : $('<div>');
            var $branch = new_$div('branch');
            var $root = new_$div('branch__root');
            var $leafs = new_$div('branch__leafs');
            $root.append(new_state(state));
            state.children.forEach(child => $leafs.append(draw_branch(child)));
            $branch.append($root);
            $branch.append($leafs);
            return $branch;
        }
        var solution_branch = draw_branch(graph);
        $('.canvas').append(solution_branch);
        draw_connections(solution_branch);
"""
SOLUTION_TEMPLATE = (
"<html>"
"<head>"
    "<meta charset='UTF-8'>"
    "<meta name='viewport'"
    "content='width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0'>"
    "<meta http-equiv='X-UA-Compatible' content='ie=edge'>"
    "<title>Solution</title>"
    "<style>%s</style>"
    "<script src='https://cdnjs.cloudflare.com/ajax/libs/jquery/3.4.1/jquery.js'></script>"
"</head>"
"<body>"
    "<div class='search-stats'>"
        "<span>Solução encontrada em %f milisegundos.</span><br>"
        "<span>Solução encontrada em %d niveis de profundidade.</span>"
    "</div>"
    "<div class='canvas'></div>"
    "<script>"
        "window.graph = %s\n" 
        "%s\n"
    "</script>"
"</body>"
"</html>"
)

EMPTY_SPACE_VALUE = 0


class EightPuzzle:
    def __init__(self, parent=None, score=0, tiles=[]):
        self.parent = parent
        self.score = score
        self.tiles = tiles
        self.depth = parent and parent.depth + 1 or 1
        self.num_of_positions = len(tiles)
        self.lateral = int(sqrt(self.num_of_positions))

    def index_of_empty_position(self):
        return self.tiles.index(EMPTY_SPACE_VALUE)

    def get_children(self):
        empty_space_idx = self.index_of_empty_position()
        children = []
        # try moving up...
        if (empty_space_idx - self.lateral) >= 0:
            src_idx = empty_space_idx
            destiny_idx = empty_space_idx - self.lateral
            temp_state = self.tiles.copy()
            temp_state[destiny_idx], temp_state[src_idx] = temp_state[src_idx], temp_state[destiny_idx]
            children.append(EightPuzzle(self, 0, temp_state))
        # try moving down...
        if (empty_space_idx + self.lateral) < self.num_of_positions:
            src_idx = empty_space_idx
            destiny_idx = empty_space_idx + self.lateral
            temp_state = self.tiles.copy()
            temp_state[destiny_idx], temp_state[src_idx] = temp_state[src_idx], temp_state[destiny_idx]
            children.append(EightPuzzle(self, 0, temp_state))
        # try moving left...
        if (empty_space_idx % self.lateral) > 0:
            src_idx = empty_space_idx
            destiny_idx = empty_space_idx - 1
            temp_state = self.tiles.copy()
            temp_state[destiny_idx], temp_state[src_idx] = temp_state[src_idx], temp_state[destiny_idx]
            children.append(EightPuzzle(self, 0, temp_state))
        # try moving right...
        if ((empty_space_idx + 1) % self.lateral) > 0:
            src_idx = empty_space_idx
            destiny_idx = empty_space_idx + 1
            temp_state = self.tiles.copy()
            temp_state[destiny_idx], temp_state[src_idx] = temp_state[src_idx], temp_state[destiny_idx]
            children.append(EightPuzzle(self, 0, temp_state))
        return children

    def __str__(self):
        return str(self.tiles)

    def __eq__(self, other):
        if not isinstance(other, EightPuzzle):
            return NotImplemented
        return self.tiles == other.tiles

    def __lt__(self, other):
        return self.score < other.score


class BestSearchFirst:
    def __init__(self, state_to_solve):
        self.state_to_solve = state_to_solve
        self.GOAL = EightPuzzle(None, 0, [1, 2, 3, 4, 5, 6, 7, 8, 0])
        self.open = [state_to_solve]
        heapify(self.open)
        self.closed = []

    def push_state_to_examine(self, state):
        state.score = self.get_heuristic_value(state)
        heappush(self.open, state)

    def substitute_state_to_examine(self, state):
        idx_element_in_heap = self.open.index(state)
        self.open[idx_element_in_heap] = self.open[-1]
        self.open.pop()
        self.push_state_to_examine(state)

    def get_heuristic_value(self, state):
        return self.get_manhattan_distance_heuristic_value(state)

    def get_manhattan_distance_heuristic_value(self, state):
        manhattan_distance_heuristic_value = 0
        def get_cordinate(index):
            return (index % state.lateral, int(index / state.lateral))
        def manhattan_distance(cord_a, cord_b):
            return abs((cord_a[0] - cord_b[0]) + (cord_a[1] - cord_b[1]))
        for index_in_state, value_in_state in enumerate(state.tiles):
            index_in_goal = self.GOAL.tiles.index(value_in_state)
            manhattan_distance_heuristic_value += manhattan_distance(get_cordinate(index_in_state), get_cordinate(index_in_goal))
        return manhattan_distance_heuristic_value

    def solve(self):
        while self.open:
            the_state = heappop(self.open)
            if the_state is None:
                break
            elif the_state == self.GOAL:
                self.closed.append(the_state)
                return self.open + self.closed, the_state, self.state_to_solve
            else:
                for child in the_state.get_children():
                    if child not in self.open and child not in self.closed:
                        self.push_state_to_examine(child)
                    elif child in self.open:
                        child_in_heap = self.open[self.open.index(child)]
                        if child.depth < child_in_heap.depth:
                            self.substitute_state_to_examine(child)
                    elif child in self.closed:
                        child_in_heap = self.closed[self.closed.index(child)]
                        if child.depth < child_in_heap.depth:
                            self.closed.remove(child)
                            self.push_state_to_examine(child)
                self.closed.append(the_state)


class StateDto:
    def __init__(self, tiles, children, depth, heuristic_score, solution_path=False):
        self.tiles = tiles
        self.children = children
        self.depth = depth
        self.heuristic_score = heuristic_score
        self.solution_path = solution_path


class MyEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            "tiles": o.tiles,
            "children": o.children,
            "depth": o.depth,
            "heuristic_score": o.heuristic_score,
            "solution_path": o.solution_path
        }


def jsonfy(solution):
    def get_solution_path(s):
        path = []
        while s is not None:
            path.append(s)
            s = s.parent
        return path

    space = solution[0]
    solution_path = get_solution_path(solution[1])
    root = solution[-1]

    def get_children(state):
        return list(filter(lambda c: c.parent == state, space))

    def populate_children(state):
        populated_children = []
        children = get_children(state)
        for child in children:
            populated_children.append(populate_children(child))
        return StateDto(state.tiles, populated_children, state.depth, state.score, state in solution_path)
    return MyEncoder().encode(populate_children(root))
    return result


if __name__ == "__main__":
    try:
        initial_state = ast.literal_eval(sys.argv[1])
        print("Buscando solução para estado: " + str(initial_state))
    except SyntaxError:
        initial_state = [3, 2, 5, 0, 4, 1, 6, 7, 8]
        print("Argumento lista contendo o estado inicial é inválido. Utilizando estado default: " + str(initial_state))
    search_method = BestSearchFirst(EightPuzzle(None, 1000, initial_state))
    start = time.time()
    solution = search_method.solve()
    end = time.time()
    search_time = (end - start) * 1000
    solution_depth = solution[1].depth
    with codecs.open("solution_presentation.html", "w", "utf-8") as file:
        file.write((SOLUTION_TEMPLATE % (MINIFIED_CSS, search_time, solution_depth, jsonfy(solution), MINIFIED_JS)))
        print ("Tempo para encontrar a solução: %.2fms, %d a níveis de profundidade." % (search_time, solution_depth))
        print ("Solução gerada no arquivo: " + os.path.abspath(file.name).replace("\\", "/"))

