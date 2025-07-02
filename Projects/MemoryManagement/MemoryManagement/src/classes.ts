// 内存块类
export class MemoryBlock {
    id: number; // 唯一标识符，用于识别每个内存块
    size: number; // 内存块的大小，以某种单位（如KB）计量
    isFree: boolean; // 布尔值，表示内存块是否为空闲状态

    constructor() {
        this.id = 0;
        this.size = 0;
        this.isFree = false;
    }
}

// 内存管理类
export class MemoryManager {
    memoryBlocks: MemoryBlock[] = [{ id: 1, size: 640, isFree: true }]; // 存放所有内存块的数组
    lastId: number = 1; // 记录最后一个被分配的内存块的ID，用于生成新内存块的唯一标识符

    // 分配内存块
    allocateMemory(block: MemoryBlock, size: number): void {
        if (block.size < size || !block.isFree) {
            console.log("内存分配失败");
            return;
        }
        if (block.size === size) {
            block.isFree = false;
            return;
        }
        const remainingSize = block.size - size;
        block.size = size;
        block.isFree = false;
        // 剩下的内存为一个新的空闲块
        this.memoryBlocks.push({
            id: ++this.lastId,
            size: remainingSize,
            isFree: true,
        });
    }

    releaseMemory(id: number): void {
        const blockIndex = this.memoryBlocks.findIndex(
            (block) => block.id === id && !block.isFree
        );
        if (blockIndex !== -1) {
            this.memoryBlocks[blockIndex].isFree = true;
            // 全局合并
            this.mergeMemory();
        }
    }

    // 全局合并
    mergeMemory(): void {
        this.memoryBlocks.sort((a, b) => a.id - b.id);
        let blockIndex = 0;
        while (blockIndex < this.memoryBlocks.length - 1) {
            // 连续两个空闲块
            if (
                this.memoryBlocks[blockIndex].isFree &&
                this.memoryBlocks[blockIndex + 1].isFree
            ) {
                this.memoryBlocks[blockIndex].size +=
                    this.memoryBlocks[blockIndex + 1].size;
                this.memoryBlocks.splice(blockIndex + 1, 1);
                continue;
            }
            blockIndex++;
        }
    }

    // 首次适应算法
    firstFit(size: number): void {
        for (let block of this.memoryBlocks) {
            if (block.isFree && block.size >= size) {
                this.allocateMemory(block, size);
                return;
            }
        }
    }

    // 最佳适应算法
    bestFit(size: number): void {
        let bestBlock: MemoryBlock | null = null;
        for (let block of this.memoryBlocks) {
            if (block.isFree && block.size >= size) {
                if (!bestBlock || block.size < bestBlock.size) {
                    bestBlock = block;
                }
            }
        }
        if (bestBlock) {
            this.allocateMemory(bestBlock, size);
        }
    }

    // 最坏适应算法
    worstFit(size: number): void {
        let worstBlock: MemoryBlock | null = null;
        for (let block of this.memoryBlocks) {
            if (block.isFree && block.size >= size) {
                if (!worstBlock || block.size > worstBlock.size) {
                    worstBlock = block;
                }
            }
        }
        if (worstBlock) {
            this.allocateMemory(worstBlock, size);
        }
    }

    // 临近适应算法
    nearFit(size: number): void {
        // 从上一次分配的内存块lastId开始查找
        let startIndex = this.memoryBlocks.findIndex(
            (block) => block.id > this.lastId
        );
        if (startIndex === -1) startIndex = 0; // 如果没找到比lastId大的块，从头开始

        // 先从startIndex到数组末尾查找
        for (let i = startIndex; i < this.memoryBlocks.length; i++) {
            if (
                this.memoryBlocks[i].isFree &&
                this.memoryBlocks[i].size >= size
            ) {
                this.allocateMemory(this.memoryBlocks[i], size);
                return;
            }
        }

        // 如果没找到，再从数组开头到startIndex查找
        for (let i = 0; i < startIndex; i++) {
            if (
                this.memoryBlocks[i].isFree &&
                this.memoryBlocks[i].size >= size
            ) {
                this.allocateMemory(this.memoryBlocks[i], size);
                return;
            }
        }
    }

    getMemoryBlocks(): MemoryBlock[] {
        return this.memoryBlocks;
    }
}
