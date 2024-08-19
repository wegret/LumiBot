基于 [Lagrange.Core](https://github.com/LagrangeDev/Lagrange.Core) 和 [NoneBot2](https://github.com/nonebot/nonebot2) 的聊天机器人。

## 插件

### `divination`

通过`crawler.py`爬取[签文]("https://www.k366.com/guanyin/28761.htm")，得到`guanyin_signs.json`后，随机抽取返回。

使用：`求签`

### `chat_reply`

使用：`/开始聊天`、`/结束聊天`

使用`ERNIE Bot SDK`调用模型，需要在`__init__.py`同目录下新建`chat_config.yaml`文件，填写token：

```
chat:
  api_type: "aistudio"
  access_token: "<access-token>"
```
