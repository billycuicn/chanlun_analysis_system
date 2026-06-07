# Windows 使用说明：中证1000缠论分析系统 v2

## 1. 解压

把压缩包解压到英文路径，例如：

```text
D:\chanlun_v2
```

不要放在中文目录、OneDrive同步目录或系统目录里，能减少权限和路径问题。

## 2. 安装 Python

安装 Python 3.10 或 3.11。

下载地址：

```text
https://www.python.org/downloads/windows/
```

安装时一定勾选：

```text
Add python.exe to PATH
```

## 3. 打开命令行

按 `Win + R`，输入：

```text
cmd
```

进入项目目录：

```bat
cd /d D:\chanlun_v2
```

## 4. 创建并启用虚拟环境

```bat
python -m venv .venv
.venv\Scripts\activate
```

看到命令行前面出现 `(.venv)`，说明虚拟环境已启用。

## 5. 安装依赖

```bat
pip install -r requirements_v2.txt
```

如果下载很慢，用国内源：

```bat
pip install -r requirements_v2.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 6. 启动系统

```bat
uvicorn chanlun_v2_app.main:app --host 127.0.0.1 --port 8010
```

看到下面这行就表示启动成功：

```text
Uvicorn running on http://127.0.0.1:8010
```

## 7. 打开网页

浏览器访问：

```text
http://127.0.0.1:8010/chanlun-v2
```

## 8. 日常使用

1. 打开页面，系统会自动补齐中证1000 30分钟K线。
2. 点击“画笔”。
3. 第一笔：在图表上点击起点，再点击终点。
4. 后续笔：系统默认从上一笔终点开始，只需要点击新的终点。
5. 点击“分析”，生成线段、中枢、买卖点。
6. 如果要写入 Obsidian，先填写 Obsidian vault 路径并保存。
7. 点击“生成报告”，系统会生成 Markdown 分析报告。

## 9. 命令脚本

也可以不用网页，直接运行脚本：

```bat
python chan_fetch.py
python chan_analyzer.py
python chan_report.py
```

## 10. 文件位置

系统运行后会自动生成 `data` 目录：

```text
data\csi852_30min.csv      K线数据
data\csi852_bi.csv         手工笔数据
data\segments.json         线段
data\zhongshu.json         中枢
data\signals.json          买卖点
data\analysis_IM_30m_*.md  分析报告
```

## 11. 下次启动

以后不需要重新安装依赖，只需要：

```bat
cd /d D:\chanlun_v2
.venv\Scripts\activate
uvicorn chanlun_v2_app.main:app --host 127.0.0.1 --port 8010
```

然后打开：

```text
http://127.0.0.1:8010/chanlun-v2
```

