from random import random, choice
from enum import Enum, auto, unique
from collections import namedtuple
import evdev
import time

Point = namedtuple('Point', ['x', 'y'])

class SnakeCollision(Exception):
    pass

@unique
class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

"""
render each frame
set the frame rate (start with 24 per sec?)
read keypad input
"""
class Game(object):
    def __init__(self, keypad_device_path, display_device):
        self.game_speed = 4 # higher is slower
        self.board = Board((32,32))
        self.keypad = evdev.InputDevice(keypad_device_path)
        self.display = display_device

    def main_loop(self):
        while True:
            # throttle loop speed using self.game_speed
            # check key input (only allow most recent to be sent to the board)
            print(self.keypad.active_keys())
            keypress = None
            if evdev.ecodes.ecodes['KEY_KP8'] in self.keypad.active_keys():
                print('UP')
                # update board state for render
                keypress = Direction.UP
            elif evdev.ecodes.ecodes['KEY_KP2'] in self.keypad.active_keys():
                print('DOWN')
                # update board state for render
                keypress = Direction.DOWN
            elif evdev.ecodes.ecodes['KEY_KP4'] in self.keypad.active_keys():
                print('LEFT')
                # update board state for render
                keypress = Direction.LEFT
            elif evdev.ecodes.ecodes['KEY_KP6'] in self.keypad.active_keys():
                print('RIGHT')
                # update board state for render
                keypress = Direction.RIGHT
            self.board.increment_state(keypress)
            # render board
            self.display.blank_display()
            for x,y,rgb in self.board.get_state():
                self.display[x,y] = rgb
            self.display.show()
            # wait for next cycle
            time.sleep(0.05 * self.game_speed)

"""
bounds
apple position
previous (snake length) number of snake head positions
collision detection (snake with snake, snake with wall, snake with apple)
    end game or
    increase snake length by 1 and move apple
walls and map generation
"""
class Board(object):
    def __init__(self, dimensions):
        self.max_x, self.max_y = dimensions
        self.snake = Snake(Point(choice(range(self.max_x)), choice(range(self.max_y))), choice(list(Direction)))
        self.snake_tail = []
        self.walls = set()
        self.apples = [Point(choice(range(self.max_x)), choice(range(self.max_y)))]
        # TODO make sure apple doesn't collide with snake head before we even start

    def increment_state(self, direction_change):
        # collision detect with walls
        if self.snake.head_position in self.walls:
            # restart
            raise SnakeCollision

        # collision detect with bounds
        if self.snake.head_position.x < 0 or self.snake.head_position.x >= 32:
            # restart
            raise SnakeCollision
        if self.snake.head_position.y < 0 or self.snake.head_position.y >= 32:
            # restart
            raise SnakeCollision

        # collision detect with tail
        for tail_position in self.snake_tail:
            if self.snake.head_position.x == tail_position.x and self.snake.head_position.y == tail_position.y:
                # restart
                raise SnakeCollision

        # collision detect with apples
        collided_apple = -1
        for i, apple_position in enumerate(self.apples):
            if self.snake.head_position.x == apple_position.x and self.snake.head_position.y == apple_position.y:
                # increase snake length
                self.snake.length += 1
                # move contacted apple
                collided_apple = i
                break

        if collided_apple != -1:
            self.apples[collided_apple] = Point(choice(range(self.max_x)), choice(range(self.max_y)))
            # TODO make sure the new point is valid

        # update snake direction
        if direction_change is not None:
            if self.snake.direction is Direction.LEFT and direction_change is not Direction.RIGHT:
                self.snake.direction = direction_change
            elif self.snake.direction is Direction.RIGHT and direction_change is not Direction.LEFT:
                self.snake.direction = direction_change
            elif self.snake.direction is Direction.UP and direction_change is not Direction.DOWN:
                self.snake.direction = direction_change
            elif self.snake.direction is Direction.DOWN and direction_change is not Direction.UP:
                self.snake.direction = direction_change

        # update self.snake_tail
        if len(self.snake_tail) == self.snake.length:
            self.snake_tail = self.snake_tail[1:]
        self.snake_tail.append(self.snake.head_position)

        # move snake head
        if self.snake.direction is Direction.UP:
            self.snake.head_position = Point(self.snake.head_position.x, self.snake.head_position.y - 1)
        elif self.snake.direction is Direction.DOWN:
            self.snake.head_position = Point(self.snake.head_position.x, self.snake.head_position.y + 1)
        elif self.snake.direction is Direction.LEFT:
            self.snake.head_position = Point(self.snake.head_position.x - 1, self.snake.head_position.y)
        elif self.snake.direction is Direction.RIGHT:
            self.snake.head_position = Point(self.snake.head_position.x + 1, self.snake.head_position.y)
        else:
            pass

    def get_state(self):
        # return grid entries (x,y,(r,g,b)) containing apples, snake head, snake tail, and wall
        yield (self.snake.head_position.x, self.snake.head_position.y, (255, 255, 255))
        for point in self.snake_tail:
            yield (point.x, point.y, (255, 255, 255))
        for point in self.apples:
            yield (point.x, point.y, (255, 0, 0))
        for point in self.walls:
            yield (point.x, point.y, (0, 0, 255))

"""
snake length
head position
direction
"""
class Snake(object):
    def __init__(self,start_point, direction, length=8):
        self.head_position = start_point
        self.direction = direction
        self.length = length
