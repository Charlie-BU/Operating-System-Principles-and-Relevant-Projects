# 每个物理块大小
BLOCKSIZE = 512
# 磁盘中物理块个数
BLOCKNUM = 512


# 磁盘物理块
class Block:
    def __init__(self, blockIndex: int, data=""):
        # 编号
        self.blockIndex = blockIndex
        # 数据
        self.data = data

    def write(self, newData: str):
        self.data = newData[:BLOCKSIZE]
        return newData[BLOCKSIZE:]

    def read(self):
        return self.data

    def isFull(self):
        return len(self.data) == BLOCKSIZE

    def append(self, newData: str) -> str:
        remainSpace = BLOCKSIZE - len(self.data)
        if remainSpace >= len(newData):
            self.data += newData
            return ""
        else:
            self.data += newData[:remainSpace]
            return newData[remainSpace:]

    def clear(self):
        self.data = ""


class FAT:
    def __init__(self):
        self.fat = []
        for i in range(BLOCKNUM):
            self.fat.append(-2)

    def findBlank(self):
        for i in range(BLOCKNUM):
            if self.fat[i] == -2:
                return i
        return -1

    def write(self, data, disk):
        start = -1
        cur = -1

        while data != "":
            newLoc = self.findBlank()
            if newLoc == -1:
                raise Exception('磁盘空间不足')
            if cur != -1:
                self.fat[cur] = newLoc
            else:
                start = newLoc
            cur = newLoc
            data = disk[cur].write(data)
            self.fat[cur] = -1

        return start

    def delete(self, start, disk):
        if start == -1:
            return

        while self.fat[start] != -1:
            disk[start].clear()
            las = self.fat[start]
            self.fat[start] = -2
            start = las

        self.fat[start] = -2
        disk[start].clear()

    def update(self, start, data, disk):
        self.delete(start, disk)
        return self.write(data, disk)

    def read(self, start, disk):
        data = ""
        while self.fat[start] != -1:
            data += disk[start].read()
            start = self.fat[start]
        data += disk[start].read()
        return data


class FCB:
    def __init__(self, name, createTime, data, fat, disk):
        # 文件名
        self.name = name
        # 创建时间
        self.createTime = createTime
        # 最后修改时间
        self.updateTime = self.createTime
        # 根据data为其分配空间
        self.start = -1

    def update(self, newData, fat, disk):
        self.start = fat.update(self.start, newData, disk)

    def delete(self, fat, disk):
        fat.delete(self.start, disk)

    def read(self, fat, disk):
        if self.start == -1:
            return ""
        else:
            return fat.read(self.start, disk)


class CatalogNode:
    def __init__(self, name, isFile, fat, disk, createTime, parent=None, data=""):
        # 路径名
        self.name = name
        # 是否为文件类型
        self.isFile = isFile
        # 父结点
        self.parent = parent
        # 创建时间
        self.createTime = createTime
        # 更新时间
        self.updateTime = self.createTime

        # 文件夹类型
        if not self.isFile:
            self.children = []
        else:
            self.data = FCB(name, createTime, data, fat, disk)
