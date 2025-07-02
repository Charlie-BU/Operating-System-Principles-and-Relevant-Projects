from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import time
import pickle
from File import *

app = Flask(__name__)
app.secret_key = 'file_management_secret_key'


class FileSystemManager:
    def __init__(self):
        self.load_file_system()
        self.current_path = ['root']

    def load_file_system(self):
        """加载文件系统数据"""
        try:
            with open('catalog', 'rb') as f:
                self.catalog = pickle.load(f)
            with open('fat', 'rb') as f:
                self.fat = pickle.load(f)
            with open('disk', 'rb') as f:
                self.disk = pickle.load(f)
        except:
            # 初始化新的文件系统
            self.catalog = []
            self.fat = FAT()
            self.disk = []
            for i in range(BLOCKNUM):
                self.disk.append(Block(i))

            # 创建根目录
            root_node = CatalogNode('root', False, self.fat, self.disk, time.localtime(time.time()))
            self.catalog.append(root_node)
            self.save_file_system()

    def save_file_system(self):
        """保存文件系统数据"""
        with open('catalog', 'wb') as f:
            pickle.dump(self.catalog, f)
        with open('fat', 'wb') as f:
            pickle.dump(self.fat, f)
        with open('disk', 'wb') as f:
            pickle.dump(self.disk, f)

    def get_current_node(self):
        """获取当前目录节点"""
        current_node = self.catalog[0]  # 根节点
        for path_part in self.current_path[1:]:  # 跳过'root'
            for child in current_node.children:
                if child.name == path_part and not child.isFile:
                    current_node = child
                    break
        return current_node

    def navigate_to(self, path_list):
        """导航到指定路径"""
        self.current_path = path_list

    def create_file(self, name, content=""):
        """创建文件"""
        current_node = self.get_current_node()

        # 检查是否已存在同名文件
        for child in current_node.children:
            if child.name == name:
                return False, "文件已存在"

        # 创建新文件
        new_file = CatalogNode(name, True, self.fat, self.disk, time.localtime(time.time()), current_node, content)
        current_node.children.append(new_file)
        self.save_file_system()
        return True, "文件创建成功"

    def create_folder(self, name):
        """创建文件夹"""
        current_node = self.get_current_node()

        # 检查是否已存在同名文件夹
        for child in current_node.children:
            if child.name == name:
                return False, "文件夹已存在"

        # 创建新文件夹
        new_folder = CatalogNode(name, False, self.fat, self.disk, time.localtime(time.time()), current_node)
        current_node.children.append(new_folder)
        self.save_file_system()
        return True, "文件夹创建成功"

    def delete_item(self, name):
        """删除文件或文件夹"""
        current_node = self.get_current_node()

        for i, child in enumerate(current_node.children):
            if child.name == name:
                if child.isFile:
                    child.data.delete(self.fat, self.disk)
                else:
                    self._delete_folder_recursive(child)
                current_node.children.pop(i)
                self.save_file_system()
                return True, "删除成功"

        return False, "文件不存在"

    def _delete_folder_recursive(self, folder_node):
        """递归删除文件夹"""
        for child in folder_node.children:
            if child.isFile:
                child.data.delete(self.fat, self.disk)
            else:
                self._delete_folder_recursive(child)

    def rename_item(self, old_name, new_name):
        """重命名文件或文件夹"""
        current_node = self.get_current_node()

        # 检查新名称是否已存在
        for child in current_node.children:
            if child.name == new_name:
                return False, "名称已存在"

        # 查找并重命名
        for child in current_node.children:
            if child.name == old_name:
                child.name = new_name
                child.updateTime = time.localtime(time.time())
                self.save_file_system()
                return True, "重命名成功"

        return False, "文件不存在"

    def read_file(self, name):
        """读取文件内容"""
        current_node = self.get_current_node()

        for child in current_node.children:
            if child.name == name and child.isFile:
                return child.data.read(self.fat, self.disk)

        return None

    def write_file(self, name, content):
        """写入文件内容"""
        current_node = self.get_current_node()

        for child in current_node.children:
            if child.name == name and child.isFile:
                child.data.update(content, self.fat, self.disk)
                child.updateTime = time.localtime(time.time())
                self.save_file_system()
                return True, "文件保存成功"

        return False, "文件不存在"

    def get_file_info(self, name):
        """获取文件信息"""
        current_node = self.get_current_node()

        for child in current_node.children:
            if child.name == name:
                return {
                    'name': child.name,
                    'isFile': child.isFile,
                    'createTime': time.strftime('%Y-%m-%d %H:%M:%S', child.createTime),
                    'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', child.updateTime),
                    'size': len(child.children) if not child.isFile else len(
                        child.data.read(self.fat, self.disk) if child.data.start != -1 else "")
                }

        return None

    def format_disk(self):
        """格式化磁盘"""
        self.fat = FAT()
        self.disk = []
        for i in range(BLOCKNUM):
            self.disk.append(Block(i))

        # 重新创建根目录
        root_node = CatalogNode('root', False, self.fat, self.disk, time.localtime(time.time()))
        self.catalog = [root_node]
        self.current_path = ['root']
        self.save_file_system()


# 全局文件系统管理器
fs_manager = FileSystemManager()


@app.route('/')
def index():
    """主页面"""
    current_node = fs_manager.get_current_node()
    files = []

    for child in current_node.children:
        file_info = {
            'name': child.name,
            'isFile': child.isFile,
            'createTime': time.strftime('%Y-%m-%d %H:%M:%S', child.createTime),
            'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', child.updateTime)
        }
        files.append(file_info)

    return render_template('index.html',
                           files=files,
                           current_path=fs_manager.current_path,
                           path_string=' > '.join(fs_manager.current_path))


@app.route('/navigate', methods=['POST'])
def navigate():
    """导航到指定目录"""
    data = request.get_json()
    path = data.get('path', [])

    # 验证路径是否有效
    try:
        fs_manager.navigate_to(path)
        current_node = fs_manager.get_current_node()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False, 'message': '无效路径'})


@app.route('/create_file', methods=['POST'])
def create_file():
    """创建文件"""
    data = request.get_json()
    name = data.get('name', '')

    if not name:
        return jsonify({'success': False, 'message': '文件名不能为空'})

    success, message = fs_manager.create_file(name)
    return jsonify({'success': success, 'message': message})


@app.route('/create_folder', methods=['POST'])
def create_folder():
    """创建文件夹"""
    data = request.get_json()
    name = data.get('name', '')

    if not name:
        return jsonify({'success': False, 'message': '文件夹名不能为空'})

    success, message = fs_manager.create_folder(name)
    return jsonify({'success': success, 'message': message})


@app.route('/delete', methods=['POST'])
def delete_item():
    """删除文件或文件夹"""
    data = request.get_json()
    name = data.get('name', '')

    success, message = fs_manager.delete_item(name)
    return jsonify({'success': success, 'message': message})


@app.route('/rename', methods=['POST'])
def rename_item():
    """重命名文件或文件夹"""
    data = request.get_json()
    old_name = data.get('old_name', '')
    new_name = data.get('new_name', '')

    if not new_name:
        return jsonify({'success': False, 'message': '新名称不能为空'})

    success, message = fs_manager.rename_item(old_name, new_name)
    return jsonify({'success': success, 'message': message})


@app.route('/edit_file/<filename>')
def edit_file(filename):
    """编辑文件页面"""
    content = fs_manager.read_file(filename)
    if content is None:
        return redirect(url_for('index'))

    return render_template('edit_file.html', filename=filename, content=content)


@app.route('/save_file', methods=['POST'])
def save_file():
    """保存文件"""
    data = request.get_json()
    filename = data.get('filename', '')
    content = data.get('content', '')

    success, message = fs_manager.write_file(filename, content)
    return jsonify({'success': success, 'message': message})


@app.route('/file_info/<filename>')
def file_info(filename):
    """获取文件信息"""
    info = fs_manager.get_file_info(filename)
    if info is None:
        return jsonify({'success': False, 'message': '文件不存在'})

    return jsonify({'success': True, 'info': info})


@app.route('/format', methods=['POST'])
def format_disk():
    """格式化磁盘"""
    fs_manager.format_disk()
    return jsonify({'success': True, 'message': '磁盘格式化成功'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
