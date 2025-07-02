from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

# 电梯系统状态
elevator_goal: list[set[int]] = [set() for _ in range(5)]  # 每个电梯的目标楼层
should_sleep: list[int] = [0] * 10  # 电梯开门状态
state: list[int] = [0] * 5  # 电梯运行状态: 0停止, 1向上, -1向下
pause: list[int] = [1] * 5  # 电梯暂停状态
floor: list[int] = [1] * 5  # 当前楼层
people_up: set[int] = set()  # 向上请求
people_down: set[int] = set()  # 向下请求


def check_elevator(elevator_id):
    idx = elevator_id - 1
    """检查并更新电梯状态"""
    if pause[idx]:
        current_floor = floor[idx]
        current_state = state[idx]

        # 首先检查当前楼层是否需要停靠
        if current_state == 1 and (current_floor in elevator_goal[idx] or current_floor in people_up):
            should_sleep[idx] = 1   # 开门
            # 更新请求集合
            people_up.discard(current_floor)
            elevator_goal[idx].discard(current_floor)

        elif current_state == -1 and (current_floor in elevator_goal[idx] or current_floor in people_down):
            should_sleep[idx + 5] = 1
            # 更新请求集合
            people_down.discard(current_floor)
            elevator_goal[idx].discard(current_floor)

        # 如果不需要停靠，则更新电梯位置
        elif current_state != 0:
            if current_state == -1:
                floor[idx] -= 1
            else:
                floor[idx] += 1

        # 更新电梯状态
        update_elevator_state(elevator_id)

        # 发送更新到前端
        socketio.emit('elevator_update', {
            'elevator_id': elevator_id,
            'floor': floor[idx],
            'state': state[idx],
            'is_open': should_sleep[idx] or should_sleep[idx + 5]
        })


def update_elevator_state(elevator_id):
    """更新电梯运行状态"""
    idx = elevator_id - 1
    goals = list(elevator_goal[idx])

    if not goals:
        state[idx] = 0
        return

    if state[idx] == -1:
        if min(goals) > floor[idx]:
            state[idx] = 1
    elif state[idx] == 1:
        if max(goals) < floor[idx]:
            state[idx] = -1
    else:  # state == 0
        if max(goals) > floor[idx]:
            state[idx] = 1
        elif min(goals) < floor[idx]:
            state[idx] = -1


class ElevatorThread(threading.Thread):
    def __init__(self, elevator_id):
        super().__init__()
        self.elevator_id = elevator_id
        self.daemon = True

    def run(self):
        while True:
            if should_sleep[self.elevator_id - 1] or should_sleep[self.elevator_id - 1 + 5]:
                time.sleep(2)
                should_sleep[self.elevator_id - 1] = 0
                should_sleep[self.elevator_id - 1 + 5] = 0

            check_elevator(self.elevator_id)
            time.sleep(1)


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('set_goal')
def handle_set_goal(data):
    """处理电梯内部按钮请求"""
    elevator_id = data['elevator']
    target_floor = data['floor']
    elevator_goal[elevator_id - 1].add(target_floor)


@socketio.on('set_up_request')
def handle_up_request(data):
    """处理向上请求"""
    floor_num = data['floor']
    people_up.add(floor_num)
    # 选择最近的电梯
    distances = [abs(floor[i] - floor_num) for i in range(5)]
    nearest_elevator = distances.index(min(distances))
    elevator_goal[nearest_elevator].add(floor_num)


@socketio.on('set_down_request')
def handle_down_request(data):
    """处理向下请求"""
    floor_num = data['floor']
    people_down.add(floor_num)
    distances = [abs(floor[i] - floor_num) for i in range(5)]
    nearest_elevator = distances.index(min(distances))
    elevator_goal[nearest_elevator].add(floor_num)


@socketio.on('toggle_pause')
def handle_pause(data):
    """处理暂停/启动请求"""
    elevator_id = data['elevator']
    pause[elevator_id - 1] = not pause[elevator_id - 1]


if __name__ == '__main__':
    # 启动电梯线程
    for i in range(5):
        ElevatorThread(i + 1).start()

    # 启动Flask应用
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
