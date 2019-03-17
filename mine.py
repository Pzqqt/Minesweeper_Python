#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import os
from time import sleep
from timeit import default_timer

# 启用调试
DEBUG = False
# ~ DEBUG = True

# 启用随机点击
# ~ RANDOM_CLICK = False
RANDOM_CLICK = True

class Block:

    __slots__ = ["x", "y", "_clicked", "_have_mine", "_num", "_flag", "sp_flag"]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._clicked = False    # 是否已点开
        self._have_mine = False  # 是否是雷
        self._num = 0            # 周围8格中雷的个数(空白格为0)
        self._flag = False       # 确定是雷(插小旗)
        self.sp_flag = set()     # 记录该方块周围可二选一的两个方块的坐标

    @property
    def have_mine(self):
        return self._have_mine

    @have_mine.setter
    def have_mine(self, value):
        if bool(value):
            self._have_mine = True

    @property
    def flag(self):
        return self._flag

    @flag.setter
    def flag(self, value):
        if not self._clicked:
            if bool(value):
                self._flag = True

    @property
    def num(self):
        return self._num

    @num.setter
    def num(self, value):
        value = int(value)
        if 0 < value < 9:
            self._num = value

    @property
    def clicked(self):
        return self._clicked

    @clicked.setter
    def clicked(self, value):
        if bool(value):
            self._clicked = True

    def print_(self, show_mine=False):
        if self._flag:
            return "♠"
        if show_mine and self._have_mine:
            return "♂"
        if not self._clicked:
            return "■"
        if self._num == 0:
            return " " + str_pad
        else:
            return str(self.num) + str_pad

class MineBoard:

    def __init__(self, h, w, mine_num):
        self.h = self.set_size(h)
        self.w = self.set_size(w)
        self.hw = self.h * self.w
        self.mn = self.set_mine_num(mine_num)
        self.board = self.gen_board_init()
        self.gen_board()

    @classmethod
    def from_seed(cls, seed):
        # 备选构造方法 指定种子
        # 若使用种子 则强制启用随机点击
        global RANDOM_CLICK
        RANDOM_CLICK = True
        cls.seed_mine_blocks, w, h = cls.analyze_seed(seed)
        cls.seed = seed
        return cls(h, w, len(cls.seed_mine_blocks))

    def set_size(self, i):
        if 9 <= int(i) <= 30:
            return int(i)
        raise Exception("范围: 9~30, 指定值: %s" % i)

    def set_mine_num(self, mine_num):
        if int(mine_num) < 10:
            raise Exception("地雷数量不得少于 10, 指定值: %s" % mine_num)
        mines_density = int(mine_num) / self.hw
        if mines_density >= 0.93:
            raise Exception("地雷密度不得高于 93%%, 当前密度: %0.2f%%" % (mines_density * 100))
        return int(mine_num)

    def print_board(self, show_mine=False):
        # 如果触雷(show_mine为True) 则不清屏以保留log
        if not show_mine:
            os_clear_screen()
        print("%s x %s" % (self.h, self.w))
        print("mine: %s flag: %s" % (self.mn, len(self.get_all_flag())))
        print("seed: " + self.seed)
        print("  ", end="")
        for x in range(self.w):
            self.print_num(x)
        print("\n", end="")
        for i in range(self.h):
            self.print_num(i, print_y=True)
            for x in range(self.w):
                print(self.board[i][x].print_(show_mine), end="")
            print("\n", end="")

    @staticmethod
    def gen_seed(mine_blocks, w, h, mn):
        # 生成种子
        # 每个雷的坐标使用4位数保存
        # 2位数保存雷区宽度 2位数保存雷区高度 最后4位数保存雷的个数
        seed = "".join(str(xy[0]).zfill(2) + str(xy[1]).zfill(2) for xy in mine_blocks) + \
               str(w).zfill(2) + str(h).zfill(2) + str(mn).zfill(4)
        return hex(int(seed))[2:]

    @staticmethod
    def analyze_seed(seed):
        # 解析种子
        try:
            seed = str(int(seed, base=16))
            w = int(seed[-8:-6])
            h = int(seed[-6:-4])
            mn = int(seed[-4:])
            seed = seed.zfill((mn + 2) * 4)
            mine_blocks = set()
            for xy in (seed[i:i+4] for i in range(0, len(seed[:-8]), 4)):
                mine_blocks.add((int(xy[:2]), int(xy[2:])))
        except:
            raise Exception("无效的种子")
        return mine_blocks, w, h

    def gen_board_init(self):
        # 初始化雷区
        board = []
        line = []
        for y in range(self.h):
            line.clear()
            for x in range(self.w):
                line.append(Block(x, y))
            board.append(line[:])
        return board

    def gen_board(self):
        # 要求: 第一次点击 此格及其周围8格一定不是雷
        # ~ first_x = random.randint(0, self.w-1)
        # ~ first_y = random.randint(0, self.h-1)
        # 一般情况下 随机点击的第一格应该是在版面的中央区域
        first_x = random.randint(self.w // 3, self.w * 2 // 3)
        first_y = random.randint(self.h // 3, self.h * 2 // 3)
        # 埋雷
        if hasattr(self, "seed_mine_blocks"):
            mine_blocks = self.seed_mine_blocks
        else:
            all_blocks = set()
            for x in range(self.w):
                for y in range(self.h):
                    if first_x-1 <= x <= first_x+1:
                        if first_y-1 <= y <= first_y+1:
                            continue
                    all_blocks.add((x, y))
            mine_blocks = random.sample(all_blocks, self.mn)
            self.seed = self.gen_seed(mine_blocks, self.w, self.h, self.mn)
        for x, y in mine_blocks:
            self.board[y][x].have_mine = True
        # 设置数字
        for y in range(self.h):
            for x in range(self.w):
                near_mn = 0
                for nx, ny in self.list_near_blocks(x, y):
                    if self.board[ny][nx].have_mine:
                        near_mn += 1
                self.board[y][x].num = near_mn
        self.click(first_x, first_y)

    def click(self, x, y):
        # 不点已点开的
        if self.board[y][x].clicked:
            return
        # 不点已插旗的
        if self.board[y][x].flag:
            return
        # BOOM!
        if self.board[y][x].have_mine:
            self.print_board(show_mine=True)
            raise Exception("你触雷了, 坐标: (%s, %s)" % (x, y))
        self.board[y][x].clicked = True
        # 如果点开的方块为空白块 则自动点开该方块周围所有的方块
        if self.board[y][x].num == 0:
            for nx, ny in self.list_near_blocks(x, y):
                self.click(nx, ny)

    def random_click(self):
        # 从所有未点开的方块中随机抽一个点开
        x, y = random.choice(list(self.get_all_not_clicked_not_flag()))
        print("Random click %s, %s" % (x, y))
        self.click(x, y)

    def set_flag(self, x, y):
        # 给方块插旗
        self.board[y][x].flag = True

    def get_all_not_clicked_not_flag(self):
        # 获取整个版面上未点开也未插旗的方块坐标集合
        not_clicked_not_flag = set()
        for y in range(self.h):
            for x in range(self.w):
                if not self.board[y][x].clicked and not self.board[y][x].flag:
                    not_clicked_not_flag.add((x, y))
        return not_clicked_not_flag

    def get_all_clicked_not_black(self):
        # 获取整个版面上已点开的非空白方块坐标集合
        clicked_not_black = set()
        for y in range(self.h):
            for x in range(self.w):
                if self.board[y][x].clicked and self.board[y][x].num != 0:
                    clicked_not_black.add((x, y))
        return clicked_not_black

    def get_all_flag(self):
        # 获取整个版面上已插旗方块坐标集合
        flag = set()
        for y in range(self.h):
            for x in range(self.w):
                if self.board[y][x].flag:
                    flag.add((x, y))
        return flag

    def list_near_blocks(self, x, y):
        # 获取该方块周围所有方块坐标集合
        near_blocks = set()
        for nx in (x-1, x, x+1):
            if nx < 0:
                continue
            if nx >= self.w:
                continue
            for ny in (y-1, y, y+1):
                if ny < 0:
                    continue
                if ny >= self.h:
                    continue
                near_blocks.add((nx, ny))
        return near_blocks

    def list_close_blocks(self, x, y):
        # 获取该方块上下左右四个方块坐标集合
        close_blocks = set()
        for nxy in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
            if 0 <= nxy[0] < self.w:
                if 0 <= nxy[1] < self.h:
                    close_blocks.add(nxy)
        return close_blocks

    def check_all_clicked(self, x, y):
        # 判断该方块是否已经解开
        # (四周不存在既没有插旗也没有点开的方块)
        for nx, ny in self.list_near_blocks(x, y):
            if not (self.board[ny][nx].clicked or self.board[ny][nx].flag):
                return False
        return True

    def get_near_not_clicked(self, x, y):
        # 获取该方块周围所有方块中未点开的方块坐标集合
        not_clicked = set()
        for nx, ny in self.list_near_blocks(x, y):
            if not self.board[ny][nx].clicked:
                not_clicked.add((nx, ny))
        return not_clicked

    def get_near_flaged(self, x, y):
        # 获取该方块周围所有方块中已插旗的方块坐标集合
        flaged = set()
        for nx, ny in self.list_near_blocks(x, y):
            if self.board[ny][nx].flag:
                flaged.add((nx, ny))
        return flaged

    def logic_1(self):
        # 逻辑1:
        # if 此方块周围未打开的方块数 == 此方块的数字
        # then 给这些方块标记为雷(插旗)
        for x, y in self.get_all_clicked_not_black():
            near_not_clicked = self.get_near_not_clicked(x, y)
            if len(near_not_clicked) == self.board[y][x].num:
                for nxy in near_not_clicked:
                    self.set_flag(*nxy)

    def logic_2(self):
        # 逻辑2:
        # if 此方块周围已插旗的方块数 == 此方块的数字 < 此方块周围未点开的方块数
        # then 点开此方块周围所有没插旗的方块
        for x, y in self.get_all_clicked_not_black():
            near_flaged = self.get_near_flaged(x, y)
            near_not_clicked = self.get_near_not_clicked(x, y)
            if len(near_flaged) == self.board[y][x].num < len(near_not_clicked):
                for nxy in near_not_clicked:
                    self.click(*nxy)
                    if DEBUG:
                        # 过程显示
                        sleep(0.02)
                        self.print_board()

    def logic_3(self):
        # 逻辑3:
        # 非常复杂的两个方块中必有一雷的逻辑推理
        # 该逻辑方法非常混乱 并且效率很低 有待改进
        for x, y in self.get_all_clicked_not_black():
            near_not_clicked = self.get_near_not_clicked(x, y)
            near_flaged = self.get_near_flaged(x, y)
            not_clicked_not_flaged = near_not_clicked - near_flaged
            if len(not_clicked_not_flaged) == 2:
                if self.board[y][x].num - len(near_flaged) == 1:
                    self.board[y][x].sp_flag = not_clicked_not_flaged
        for x, y in self.get_all_clicked_not_black():
            if not self.check_all_clicked(x, y):
                ignore_blocks = None
                for nx, ny in self.list_close_blocks(x, y):
                    if self.board[ny][nx].sp_flag:
                        if len(self.board[ny][nx].sp_flag & self.get_near_not_clicked(x, y)) == 2:
                            ignore_blocks = self.board[ny][nx].sp_flag
                            break
                if ignore_blocks:
                    # 逻辑1 变种
                    near_not_clicked = self.get_near_not_clicked(x, y) - ignore_blocks
                    if len(near_not_clicked) == (self.board[y][x].num - 1):
                        for nxy in near_not_clicked:
                            self.set_flag(*nxy)
                    # 逻辑2 变种
                    near_flaged = self.get_near_flaged(x, y)
                    if len(near_flaged) == (self.board[y][x].num - 1) < len(near_not_clicked):
                        (igx1, igy1), (igx2, igy2) = ignore_blocks
                        if not (self.board[igy1][igx1].flag or self.board[igy2][igx2].flag):
                            for nxy in near_not_clicked:
                                self.click(*nxy)

    def logic_4(self):
        # 逻辑4:
        # if 已插旗方块数 == 总雷数
        # then 点开所有未点开未插旗的方块
        for xy in self.get_all_not_clicked_not_flag():
            self.click(*xy)

    def logic_5(self):
        # 逻辑5:
        # if 未插旗数 == 1
        # then 点开除二选一的两个方块之外的所有方块
        for x, y in self.get_all_clicked_not_black():
            if (not self.check_all_clicked(x, y)) and self.board[y][x].sp_flag:
                for nxy in self.get_all_not_clicked_not_flag():
                    if nxy not in self.board[y][x].sp_flag:
                        self.click(*nxy)

    def logic_start(self):
        # 开始解题
        # 逻辑5 只允许执行一次 否则可能会陷入无限循环
        logic_5_run_once = False
        time_start = default_timer()
        while len(self.get_all_flag()) < self.mn:
            ncn = len(self.get_all_not_clicked_not_flag())
            self.logic_1()
            self.logic_2()
            self.logic_3()
            new_ncn = len(self.get_all_not_clicked_not_flag())
            if ncn == new_ncn:
                # 如果仍有80%的方块未被点开 则随机点开一个
                if RANDOM_CLICK and new_ncn / self.hw >= 0.8:
                    self.random_click()
                elif (self.mn - len(self.get_all_flag())) == 1 and (not logic_5_run_once):
                    self.logic_5()
                    logic_5_run_once = True
                else:
                    break
        else:
            self.logic_4()
        time_cost = default_timer() - time_start
        self.print_board()
        print("耗时: %0.6fs" % time_cost)

    @staticmethod
    def print_num(x, print_y=False):
        # 格式化数字字符输出
        if is_win() or print_y:
            print(" " + str(x), end="") if x < 10 else print(str(x), end="")
        else:
            print(str(x), end="") if x < 10 else print(str(x)[-1], end="")

def is_win():
    # 判断是否为Windows系统环境
    return os.name == "nt"

def os_clear_screen():
    # 清屏
    os.system("cls") if is_win() else os.system("clear")

def main():
    # 9*9 10(初级)，16*16 40 (中级)，16*30 99(高级)
    # ~ mb = MineBoard(9, 9, 10)
    # ~ mb = MineBoard(16, 16, 40)
    mb = MineBoard(16, 30, 99)
    # ~ seed = "583e2e3a1230d7fa3415920384ac1395a69aa60944b8344832b18873a8a33f51287aeda9beea4e27b7f7b567ea16d041030df76088257ea6db2be8516ee87fb3d65700ccd28"
    # ~ mb = MineBoard.from_seed(seed)
    mb.logic_start()

# 终端打印字符填充
str_pad = " " if is_win() else ""

if __name__ == "__main__":
    main()
