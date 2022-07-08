__中文简体__|| [English](./README.md) 
# pe2pic
Small visualizator for PE files

# 入门指南
通过以下方式安装依赖项:

```console
pip install -r requirements.txt
```

# 用法

```
usage: pe2pic.py [-h] --infile INFILE [--outfile OUTFILE] [--double]
                 [--minheight MINHEIGHT]

PE可视化工具

可选项:
  -h, --help            显示帮助消息并退出
  --infile INFILE       输入文件
  --outfile OUTFILE     输出文件
  --double              双层截面视图？
  --minheight MINHEIGHT 输出图像的最小高度

```

# 演示

双视图:

![](img/demo2.png)

单一视图:

![](img/demo1.png)
