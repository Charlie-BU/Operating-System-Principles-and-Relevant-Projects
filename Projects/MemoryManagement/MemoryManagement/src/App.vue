<template>
    <h1 style='text-align: center'>动态分区分配方式模拟</h1>

    <div class='container'>
        <div class='half'>
            <el-button-group>
                <el-button type='primary' plain size='large' round @click="runPagingAllocationSimulation('firstFit')">
                    首次适应算法
                </el-button>
                <el-button type='primary' plain size='large' round @click="runPagingAllocationSimulation('bestFit')">
                    最佳适应算法
                </el-button>
                <el-button type='primary' plain size='large' round @click="runPagingAllocationSimulation('worstFit')">
                    最差适应算法
                </el-button>
                <el-button type='primary' plain size='large' round @click="runPagingAllocationSimulation('nearFit')">
                    邻近适应算法
                </el-button>
                <el-button type='primary' plain size='large' round @click='restartMemoryManager'>重置</el-button>
            </el-button-group>
            <div style="margin-top: 20px; width: 80%;">
                <div class="operation-info" v-if="currentTask > 0 && currentTask <= taskSequence.length">
                    <el-alert :title="'当前操作: ' + taskSequence[currentTask - 1].description" type="info"
                        :closable="false" style="margin-bottom: 10px;" />
                </div>
            </div>
            <br />
            <div class="display-section" style='display: flex; justify-content: space-around; width: 100%'>
                <div>
                    <h3 style="text-align: center;">任务列表</h3>
                    <el-table stripe :data='taskSequence' style='width: 360px'>
                        <el-table-column prop='id' label='任务序号' width='120' align='center' />
                        <el-table-column prop='description' label='任务内容' width='240' align='center' />
                    </el-table>
                </div>

                <div>
                    <h3 style="text-align: center;">内存分配情况</h3>
                    <el-table :data='memoryBlocks' stripe style='width: 360px'>
                        <el-table-column prop='id' label='分区 ID' width='120' align='center' />
                        <el-table-column prop='size' label='大小 (K)' width='120' align='center' />
                        <el-table-column prop='isFree' label='是否空闲' width='120' align='center'>
                            <template #default='scope'>
                                {{ scope.row.isFree ? '是' : '否' }}
                            </template>
                        </el-table-column>
                    </el-table>
                </div>

                <div class="memory-bar"
                    style="width: 5%; border: 1px solid #ccc; margin-bottom: 10px; flex-direction: column-reverse; height: 600px;">
                    <div v-for="block in memoryBlocks" :key="block.id" :style="{
                        height: (block.size / 640 * 100) + '%',
                        backgroundColor: block.isFree ? '#91cc75' : '#ee6666',
                        width: '100%',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        color: '#fff',
                        borderTop: '1px dashed #fff',
                        fontSize: '13px'
                    }">
                        分区ID：{{ block.id }}<br>{{ block.isFree ? "空闲" : "占用" }}<br>{{ block.size }}K
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang='ts'>
import { MemoryBlock, MemoryManager } from './classes'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

// 动态分区分配方式模拟
const memoryManager = ref(new MemoryManager())
const memoryBlocks = ref<MemoryBlock[]>(memoryManager.value.getMemoryBlocks())
const currentTask = ref(0)

const taskSequence = ref([
    { id: 1, description: '作业 1 申请 130K' },
    { id: 2, description: '作业 2 申请 60K' },
    { id: 3, description: '作业 3 申请 100K' },
    { id: 4, description: '作业 2 释放 60K' },
    { id: 5, description: '作业 4 申请 200K' },
    { id: 6, description: '作业 3 释放 100K' },
    { id: 7, description: '作业 1 释放 130K' },
    { id: 8, description: '作业 5 申请 140K' },
    { id: 9, description: '作业 6 申请 60K' },
    { id: 10, description: '作业 7 申请 50K' },
    { id: 11, description: '作业 6 释放 60K' }
])

const funcCallSequence = (algorithm: string) => {
    const fitMap: Record<string, (size: number) => void> = {
        firstFit: (size: number) => memoryManager.value.firstFit(size),
        bestFit: (size: number) => memoryManager.value.bestFit(size),
        worstFit: (size: number) => memoryManager.value.worstFit(size),
        nearFit: (size: number) => memoryManager.value.nearFit(size)
    };

    const func = fitMap[algorithm];
    if (!func) return [];
    return [
        () => func(130),
        () => func(60),
        () => func(100),
        () => memoryManager.value.releaseMemory(2),
        () => func(200),
        () => memoryManager.value.releaseMemory(3),
        () => memoryManager.value.releaseMemory(1),
        () => func(140),
        () => func(60),
        () => func(50),
        () => memoryManager.value.releaseMemory(6)
    ]
}


const runPagingAllocationSimulation = (algorithmType: string) => {
    let sequence: (() => void)[] = funcCallSequence(algorithmType)
    let message: string = ''
    if (algorithmType === 'firstFit') {
        message = '模拟首次适应算法：'
    } else if (algorithmType === 'bestFit') {
        message = '模拟最佳适应算法：'
    }
    if (currentTask.value < sequence.length) {
        sequence[currentTask.value]()
        ElMessage({
            showClose: true,
            message: message + taskSequence.value[currentTask.value].description,
            type: 'success',
            duration: 2000
        })
        currentTask.value++
        // 确保更新内存块数据
        memoryBlocks.value = [...memoryManager.value.getMemoryBlocks()]
    } else {
        ElMessage({
            showClose: true,
            message: '动态分区分配方式模拟已完成',
            type: 'success',
            duration: 2000
        })
    }
}

const restartMemoryManager = () => {
    memoryManager.value = new MemoryManager()
    // 确保更新内存块数据
    memoryBlocks.value = [...memoryManager.value.getMemoryBlocks()]
    currentTask.value = 0
    ElMessage({
        showClose: true,
        message: '动态分区分配方式模拟已重置',
        type: 'warning',
        duration: 2000
    })
}
</script>

<style>
.container {
    width: 100%;
}

.half {
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* 添加内存条可视化相关样式 */
.memory-visualization {
    padding: 15px;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    background-color: #fff;
}

.memory-bar div {
    transition: all 0.5s ease;
    overflow: hidden;
    font-size: 12px;
    text-align: center;
}
</style>
