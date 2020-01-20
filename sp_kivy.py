"""
Sliding tile puzzle
"""
import time
from random import shuffle
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window

class Card(Button):
    """
    Card
      y                  row
    100:   0,   1,   2, | 0
     50:   3,   4,   5, | 1
      0:   6,   7,   8  | 2
    --------------------
           0,  70, 140  : x
    --------------------
           0    1    2  : col
    """
    def __init__(self, rgb, cell_num, board, **kwargs):
        kwargs["on_press"] = self.click_handler
        super().__init__(**kwargs)
        self.rgb = rgb
        self.initial_cellnum = cell_num
        self.cell_num = cell_num
        self.num_cols = board.cols
        self.cell_movex = board.movex # {0:0, 1:70, 2:140}
        self.cell_movey = board.movey # {0:100, 1:50, 2:0}
        self.move_handler = board.move
        self.cards = board.children
        self.face_value = kwargs["text"]
        self.trigger_rerunner = board.trigger_rerunner
        self.check_rerunner = board.check_rerunner

    def on_size(self, pos_size, *args):
        """
        kivy: on_size event
        """
        # print("Card.on_size", self.face_value, pos_size)
        row_num = self.calc_row_num()
        col_num = self.calc_col_num()
        self.cell_movex[col_num] = self.pos[0]
        self.cell_movey[row_num] = self.pos[1]
        if self == self.cards[0]:
            # print("last", self.face_value, self.cell_num)
            self.trigger_rerunner()

    def __str__(self):
        return "(" + str(self.x) + "," + str(self.y) + "," + str(self.width) +\
            "," + str(self.height) + ")"

    def click_handler(self, instance):
        """
        click_handler
        """
        print("Card.click_handler", self.face_value, self.cell_num, instance.width, instance.height, instance.pos[0], instance.pos[1])
        self.move_handler(self, instance)

    def calc_row_num(self):
        """
        calc_row_num
        """
        return int(self.cell_num / self.num_cols)

    def calc_col_num(self):
        """
        calc_col_num
        """
        return self.cell_num % self.num_cols

    def on_move_end(self, anim, widget_instance):
        """
        on_move_end
        """
        print("Card.on_move_end", self.face_value, self.cell_num, widget_instance.pos)
        self.check_rerunner()

    def animate_move(self, instance):
        """
        animate_move
        """
        col_num = self.calc_col_num() # += 1
        row_num = self.calc_row_num()
        # print(row_num, col_num, self.cell_num, self.cell_movex[row_num], self.cell_movey[col_num])
        animation = Animation(pos=(self.cell_movex[col_num], self.cell_movey[row_num]), d=0.2)
        animation.bind(on_complete=self.on_move_end)
        animation.start(instance)

    def move_up(self, instance):
        """
        move_up
        """
        row_num = self.calc_row_num()
        if row_num == 0:
            return
        self.cell_num -= self.num_cols
        self.animate_move(instance)

    def move_right(self, instance):
        """
        move_right
        """
        col_num = self.calc_col_num()
        if col_num == self.num_cols - 1:
            return
        self.cell_num += 1
        self.animate_move(instance)

    def move_down(self, instance):
        """
        move_down
        """
        row_num = self.calc_row_num()
        if row_num == self.num_cols - 1:
            return
        self.cell_num += self.num_cols
        self.animate_move(instance)

    def move_left(self, instance):
        """
        move_left
        """
        col_num = self.calc_col_num()
        if col_num == 0:
            return
        self.cell_num -= 1
        self.animate_move(instance)

class Board(GridLayout):
    """
    Board
    """
    def __init__(self, **kwargs):
        super(Board, self).__init__(**kwargs)
        self.cols = kwargs["cols"]
        num_slots = self.cols**2
        board = []
        for i in range(1, num_slots):
            board.append(i)

        while True:
            shuffle(board)
            num_inversions = self.count_inversion(board)
            if num_inversions % 2 == 0:
                # Since the empty is initially in the first row from the bottom, this checks the
                # solvable board. See count_inversion() for the details.
                break

        print(board)
        self.movex = {}
        self.movey = {}
        self.moves = []
        self.stored_moves = []
        self.rerunner_moves = []
        self.trigger_rerunner = Clock.create_trigger(self.rerunner)
        self.trigger_dorerun = Clock.create_trigger(self.do_rerun)
        self.scheduled_rerun_time = 0
        self.scheduled_rerun = None
        for i in range(0, num_slots-1):
            self.add_widget(Card((255, 255, 0), i, self,\
                text=str(board[i]), color=[1, 1, 0, 1.0]))
        self.free_cell = num_slots - 1

    def move(self, cell, widget_instance):
        """
        move
        """
        if cell.cell_num - self.cols == self.free_cell:
            self.free_cell = cell.cell_num
            cell.move_up(widget_instance)
            self.moves.append((cell, widget_instance))
        elif cell.calc_col_num() < self.cols - 1 and cell.cell_num + 1 == self.free_cell:
            self.free_cell = cell.cell_num
            cell.move_right(widget_instance)
            self.moves.append((cell, widget_instance))
        elif cell.cell_num + self.cols == self.free_cell:
            self.free_cell = cell.cell_num
            cell.move_down(widget_instance)
            self.moves.append((cell, widget_instance))
        elif cell.calc_col_num() > 0 and cell.cell_num - 1 == self.free_cell:
            self.free_cell = cell.cell_num
            cell.move_left(widget_instance)
            self.moves.append((cell, widget_instance))
        board = [self.cols**2] * (self.cols**2) # Empty cell gets #cols, so inversion_count treats board solved when the cards
        for card in self.children: # are in the order and the empty slot is in the bottom right.
            board[card.cell_num] = int(card.face_value)
        # print("move", board)
        inversion = self.count_inversion(board)
        if inversion == 0:
            print("solved")

    def count_inversion(self, board):
        """
        param board List of card face values\n

        An inversion is when a cell precedes another cell with a lower number on it. The solution
        state has zero inversions. For example, if, in a 3 x 3 grid, number 8 is top left, then
        there will be 7 inversions from this card, as numbers 1-7 come after it. To explain it
        another way, an inversion is a pair of cards (a,b) such that a appears before b, but a > b.
          8, 4, 3  inversions: 7, 3, 2
          2, 6, 1              1, 2, 0
          7, 5                 1, 0
        The formula says:
          If the grid width is odd, then the number of inversions in a solvable situation is even.
          If the grid width is even, and the blank is on an even row counting from the bottom
            (second-last, fourth-last etc), then
              the number of inversions in a solvable situation is odd.
          If the grid width is even, and the blank is on an odd row counting from the bottom
            (last, third-last, fifth-last etc) then
              the number of inversions in a solvable situation is even.
        That gives us this formula for determining solvability:
          ((grid width odd) && (#inversions even))  ||
          ((grid width even) && ((blank on odd row from bottom) == (#inversions even)))
        """
        inversions_all = 0
        for i, val in enumerate(board[0:-1]):
            for after in board[i+1:len(board)]:
                if after < val:
                    inversions_all += 1
        # print("inversions_all=" + str(inversions_all))
        return inversions_all

    def on_size(self, *args):
        """
        on_size
        """
        self.free_cell = self.cols**2 - 1 # the last one
        for card in self.children:
            card.cell_num = card.initial_cellnum

    def rerunner(self, *args):
        """
        rerunner
        """
        if self.moves and not self.rerunner_moves:
            if self.scheduled_rerun_time > 0:
                self.scheduled_rerun.cancel()
            self.scheduled_rerun_time = time.time()
            self.scheduled_rerun = Clock.schedule_once(self.do_rerun, 0.5)

    def do_rerun(self, *args):
        """
        do_rerun
        """
        self.scheduled_rerun_time = 0
        print("Board.do_rerun", len(self.moves), "moves", self.movex, self.movey)
        if self.rerunner_moves:
            move = self.rerunner_moves.pop(0)
            self.move(move[0], move[1])
            return
        if self.moves and not self.rerunner_moves:
            self.rerunner_moves = self.moves.copy()
            self.stored_moves = self.moves.copy()
            self.moves.clear()
            move = self.rerunner_moves.pop(0)
            self.move(move[0], move[1])

    def check_rerunner(self):
        """
        check_rerunner
        """
        if self.rerunner_moves:
            self.trigger_dorerun()

class Header(BoxLayout):
    """
    Header
    """
    def __init__(self, create_board, **kwargs):
        kwargs["orientation"] = "horizontal"
        super(Header, self).__init__(**kwargs)
        self.add_widget(Button(text="3x3", on_press=lambda btn: create_board(3)))
        self.add_widget(Button(text="4x4", on_press=lambda btn: create_board(4)))
        self.add_widget(Button(text="5x5", on_press=lambda btn: create_board(5)))
        self.add_widget(Button(text="6x6", on_press=lambda btn: create_board(6)))
        self.add_widget(Button(text="7x7", on_press=lambda btn: create_board(7)))

class Ui(BoxLayout):
    """
    Ui
    """
    def __init__(self, **kwargs):
        super(Ui, self).__init__(**kwargs)
        self.header = Header(self.create_board, size_hint=(1, None), height="60sp")
        self.board = None
        #self.board = Board(cols=5, size_hint=(1, 1), spacing=0, padding=0)
        self.add_widget(self.header)
        #self.add_widget(self.board)

    def create_board(self, num_cols):
        """
        create_board
        """
        if self.board is not None:
            self.board.clear_widgets()
            self.remove_widget(self.board)
        self.board = Board(cols=num_cols, size_hint=(1, 1), spacing=0, padding=0)
        self.add_widget(self.board)

class SlidePuzzle(App):
    """
    SlidePuzzle
    """
    def build(self):
        myui = Ui(orientation="vertical", spacing=0, padding=0)
        # myui.board.count_inversion([8, 4, 3, 2, 6, 1, 7, 5])
        # myui.board.count_inversion([8, 5, 4, 2, 6, 1, 3, 7])
        # myui.board.count_inversion([1, 2, 3, 4, 5, 6, 7, 8])
        return myui

if __name__ == '__main__':
    # Window.size = (420, 800) # (210, 200)
    Window.clearcolor = (1, 1, 0, 0.1)
    SlidePuzzle().run()
